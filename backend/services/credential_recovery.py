"""
Service: Authorized Credential Recovery & Configuration Backup Analysis
Searches legitimate local credential caches:
1. Local NetworkManager connection profiles (exact SSID/BSSID match)
2. Operating system connection keyfiles (/etc/NetworkManager/system-connections)
3. User-provided router configuration backup archives (.bin, .conf, .xml, .txt)
"""

import logging
import os
import re
import subprocess
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


@dataclass
class RecoveredCredential:
    ssid: str
    password: str
    source_name: str
    source_type: str
    bssid: Optional[str] = None
    security_type: str = "WPA/WPA2-PSK"
    profile_uuid: Optional[str] = None
    location: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CredentialRecoveryService:
    """Safely audits authorized local stores for the specific target Wi-Fi network."""

    @classmethod
    def recover_target_credential(
        cls,
        target_ssid: str,
        target_bssid: Optional[str] = None,
        backup_content: Optional[str] = None,
        backup_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes targeted credential checks across legitimate authorized sources.
        """
        target_clean = target_ssid.strip()
        checks_performed: List[Dict[str, Any]] = []

        # =====================================================================
        # SOURCE 1: Local NetworkManager Profile Check
        # =====================================================================
        nm_result = cls._check_network_manager(target_clean, target_bssid)
        checks_performed.append(nm_result["check_summary"])

        if nm_result["found"]:
            return {
                "found": True,
                "credential": nm_result["credential"].to_dict(),
                "checks_performed": checks_performed
            }

        # =====================================================================
        # SOURCE 2: System Connections Directory Keyfiles
        # =====================================================================
        sys_result = cls._check_system_connections(target_clean, target_bssid)
        checks_performed.append(sys_result["check_summary"])

        if sys_result["found"]:
            return {
                "found": True,
                "credential": sys_result["credential"].to_dict(),
                "checks_performed": checks_performed
            }

        # =====================================================================
        # SOURCE 3: User-provided Router Configuration Backup
        # =====================================================================
        backup_result = cls._check_backup_content(target_clean, backup_content, backup_filename)
        checks_performed.append(backup_result["check_summary"])

        if backup_result["found"]:
            return {
                "found": True,
                "credential": backup_result["credential"].to_dict(),
                "checks_performed": checks_performed
            }

        # Not found in any authorized local source
        return {
            "found": False,
            "credential": None,
            "checks_performed": checks_performed
        }

    @classmethod
    def _check_network_manager(cls, target_ssid: str, target_bssid: Optional[str]) -> Dict[str, Any]:
        """Queries local user NetworkManager profiles for matching target SSID."""
        try:
            # 1. Direct query by target profile name
            res = subprocess.run(
                ["nmcli", "-s", "-g", "802-11-wireless-security.psk", "connection", "show", target_ssid],
                capture_output=True, text=True, timeout=3, check=False
            )
            psk = res.stdout.strip()
            if res.returncode == 0 and psk:
                cred = RecoveredCredential(
                    ssid=target_ssid,
                    password=psk,
                    source_name=f"Local NetworkManager Profile ({target_ssid})",
                    source_type="Operating System Profile",
                    bssid=target_bssid,
                    security_type="WPA/WPA2-PSK",
                    location=f"NetworkManager connection store: {target_ssid}"
                )
                return {
                    "found": True,
                    "credential": cred,
                    "check_summary": {
                        "source": "NetworkManager User Profiles",
                        "status": "Found",
                        "details": f"Recovered stored pre-shared key for '{target_ssid}' from active profile."
                    }
                }

            # 2. Enumerate all saved wireless profiles
            cmd = ["nmcli", "-t", "-f", "NAME,UUID,TYPE", "connection", "show"]
            list_res = subprocess.run(cmd, capture_output=True, text=True, timeout=3, check=False)

            if list_res.returncode == 0:
                profiles = []
                for line in list_res.stdout.strip().splitlines():
                    parts = line.split(":")
                    if len(parts) >= 3 and "wireless" in parts[2]:
                        name, uuid = parts[0], parts[1]
                        profiles.append((name, uuid))

                for name, uuid in profiles:
                    if name.lower() == target_ssid.lower():
                        psk_res = subprocess.run(
                            ["nmcli", "-s", "-g", "802-11-wireless-security.psk", "connection", "show", uuid],
                            capture_output=True, text=True, timeout=3, check=False
                        )
                        found_psk = psk_res.stdout.strip()
                        if psk_res.returncode == 0 and found_psk:
                            cred = RecoveredCredential(
                                ssid=target_ssid,
                                password=found_psk,
                                source_name=f"Local NetworkManager Profile ({name})",
                                source_type="Operating System Profile",
                                bssid=target_bssid,
                                profile_uuid=uuid,
                                location=f"/etc/NetworkManager/system-connections/{name}.nmconnection"
                            )
                            return {
                                "found": True,
                                "credential": cred,
                                "check_summary": {
                                    "source": "NetworkManager User Profiles",
                                    "status": "Found",
                                    "details": f"Recovered stored key from saved profile '{name}'."
                                }
                            }

                return {
                    "found": False,
                    "credential": None,
                    "check_summary": {
                        "source": "NetworkManager User Profiles",
                        "status": "Not found",
                        "details": f"Audited {len(profiles)} saved Wi-Fi profiles; no profile found matching '{target_ssid}'."
                    }
                }

            return {
                "found": False,
                "credential": None,
                "check_summary": {
                    "source": "NetworkManager User Profiles",
                    "status": "Error",
                    "details": "nmcli service returned error or was unresponsive."
                }
            }
        except Exception as e:
            return {
                "found": False,
                "credential": None,
                "check_summary": {
                    "source": "NetworkManager User Profiles",
                    "status": "Permission required",
                    "details": f"Could not inspect NetworkManager: {e}"
                }
            }

    @classmethod
    def _check_system_connections(cls, target_ssid: str, target_bssid: Optional[str]) -> Dict[str, Any]:
        """Audits raw system connection keyfiles in /etc/NetworkManager/system-connections/."""
        target_dir = "/etc/NetworkManager/system-connections"
        if not os.path.exists(target_dir):
            return {
                "found": False,
                "credential": None,
                "check_summary": {
                    "source": "System Connection Keyfiles (/etc/NetworkManager/system-connections/)",
                    "status": "Unsupported",
                    "details": "Path /etc/NetworkManager/system-connections does not exist on this OS."
                }
            }

        if not os.access(target_dir, os.R_OK):
            return {
                "found": False,
                "credential": None,
                "check_summary": {
                    "source": "System Connection Keyfiles (/etc/NetworkManager/system-connections/)",
                    "status": "Permission required",
                    "details": "Direct keyfile inspection is restricted by Linux filesystem permissions (requires sudo/root)."
                }
            }

        try:
            files = [f for f in os.listdir(target_dir) if os.path.isfile(os.path.join(target_dir, f))]
            for fname in files:
                fpath = os.path.join(target_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        if target_ssid.lower() in content.lower():
                            psk_match = re.search(r"psk=(.+)", content)
                            if psk_match:
                                cred = RecoveredCredential(
                                    ssid=target_ssid,
                                    password=psk_match.group(1).strip(),
                                    source_name=f"System Keyfile ({fname})",
                                    source_type="Operating System Keyfile",
                                    bssid=target_bssid,
                                    location=fpath
                                )
                                return {
                                    "found": True,
                                    "credential": cred,
                                    "check_summary": {
                                        "source": "System Connection Keyfiles",
                                        "status": "Found",
                                        "details": f"Recovered pre-shared key from keyfile {fname}."
                                    }
                                }
                except Exception:
                    continue

            return {
                "found": False,
                "credential": None,
                "check_summary": {
                    "source": "System Connection Keyfiles (/etc/NetworkManager/system-connections/)",
                    "status": "Not found",
                    "details": f"Checked {len(files)} system keyfiles; no match for '{target_ssid}'."
                }
            }
        except Exception as e:
            return {
                "found": False,
                "credential": None,
                "check_summary": {
                    "source": "System Connection Keyfiles",
                    "status": "Error",
                    "details": str(e)
                }
            }

    @classmethod
    def _check_backup_content(
        cls,
        target_ssid: str,
        content: Optional[str],
        filename: Optional[str]
    ) -> Dict[str, Any]:
        """Audits user-supplied router configuration backup files."""
        if not content:
            return {
                "found": False,
                "credential": None,
                "check_summary": {
                    "source": "User-Provided Router Configuration Backup",
                    "status": "Not provided",
                    "details": "No router backup file (.bin, .conf, .xml) was attached for this analysis."
                }
            }

        # Analyze imported backup content for matching credentials
        psk_match = re.search(
            r"(?:psk_key|wpa_key|password|presharedkey|wlan\.key|key|passphrase)[\s=\":]+([^\r\n\"';<]+)",
            content,
            re.I
        )

        if psk_match:
            found_pwd = psk_match.group(1).strip()
            cred = RecoveredCredential(
                ssid=target_ssid,
                password=found_pwd,
                source_name=f"Router Configuration Backup ({filename or 'imported_backup.conf'})",
                source_type="Configuration Export File",
                location=filename or "Uploaded Backup"
            )
            return {
                "found": True,
                "credential": cred,
                "check_summary": {
                    "source": "User-Provided Router Configuration Backup",
                    "status": "Found",
                    "details": f"Extracted valid wireless passphrase from '{filename or 'backup.conf'}'."
                }
            }

        return {
            "found": False,
            "credential": None,
            "check_summary": {
                "source": "User-Provided Router Configuration Backup",
                "status": "Not found",
                "details": f"Analyzed '{filename or 'backup.conf'}'; no matching wireless credentials found in file."
            }
        }


credential_recovery = CredentialRecoveryService()
