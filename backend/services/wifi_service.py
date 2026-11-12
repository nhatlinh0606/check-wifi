"""
Wi-Fi Service
Discovers nearby wireless access points using standard Linux OS APIs (nmcli).
Extracts SSID, BSSID, Signal strength, Channel, Security, Band, and Vendor OUI.
Provides safe local Wi-Fi password recovery from saved NetworkManager connection profiles.
Strictly passive and read-only.
"""

import logging
import re
import subprocess
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any

from modules.router_identifier import RouterIdentifier

logger = logging.getLogger(__name__)


@dataclass
class WifiNetwork:
    ssid: str
    bssid: str
    channel: int
    signal: int
    bars: str
    security: str
    band: str
    vendor: str
    is_tplink: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class WifiService:
    def __init__(self):
        self.router_identifier = RouterIdentifier()

    def scan_networks(self, rescan: bool = True) -> List[WifiNetwork]:
        """
        Scans for visible Wi-Fi access points via nmcli.
        """
        cmd = ["nmcli", "-t", "-f", "SSID,BSSID,CHAN,BARS,SIGNAL,SECURITY", "dev", "wifi", "list"]
        if rescan:
            cmd.extend(["--rescan", "yes"])

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10, check=False)
            if res.returncode != 0:
                logger.warning(f"nmcli command returned error: {res.stderr}")
                return []
            return self._parse_nmcli_output(res.stdout)
        except Exception as e:
            logger.error(f"Error scanning Wi-Fi networks: {e}")
            return []

    def _parse_nmcli_output(self, output: str) -> List[WifiNetwork]:
        networks: List[WifiNetwork] = []
        seen_bssids = set()

        for line in output.strip().splitlines():
            if not line.strip():
                continue

            # nmcli escapes colons in BSSIDs with backslashes: e.g. 54\:04\:63\:23\:75\:31
            escaped_marker = "__COLON__"
            safe_line = line.replace(r"\:", escaped_marker)
            parts = safe_line.split(":")

            if len(parts) >= 6:
                raw_ssid = parts[0].replace(escaped_marker, ":").strip()
                raw_bssid = parts[1].replace(escaped_marker, ":").strip()
                raw_chan = parts[2].replace(escaped_marker, ":").strip()
                raw_bars = parts[3].replace(escaped_marker, ":").strip()
                raw_signal = parts[4].replace(escaped_marker, ":").strip()
                raw_security = parts[5].replace(escaped_marker, ":").strip() if len(parts) > 5 else "None"

                ssid = raw_ssid if raw_ssid else "[Hidden SSID]"
                bssid = raw_bssid.upper()

                if bssid in seen_bssids:
                    continue
                seen_bssids.add(bssid)

                try:
                    channel = int(raw_chan)
                except ValueError:
                    channel = 0

                try:
                    signal = int(raw_signal)
                except ValueError:
                    signal = 0

                band = "2.4 GHz" if channel <= 14 else "5 GHz"
                vendor = self.router_identifier.lookup_mac_vendor(bssid)
                is_tplink = "TP-LINK" in vendor.upper() or bool(re.search(r"\b(tplink|tp-link|archer|deco)\b", ssid, re.I))

                networks.append(
                    WifiNetwork(
                        ssid=ssid,
                        bssid=bssid,
                        channel=channel,
                        signal=signal,
                        bars=raw_bars,
                        security=raw_security,
                        band=band,
                        vendor=vendor,
                        is_tplink=is_tplink
                    )
                )

        # Sort by signal strength descending
        return sorted(networks, key=lambda x: x.signal, reverse=True)

    def get_saved_profiles(self) -> List[Dict[str, Any]]:
        """
        Lists saved Wi-Fi connections on the local machine via nmcli.
        """
        cmd = ["nmcli", "-t", "-f", "NAME,UUID,TYPE,DEVICE", "connection", "show"]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5, check=False)
            if res.returncode != 0:
                return []

            profiles = []
            for line in res.stdout.strip().splitlines():
                parts = line.split(":")
                if len(parts) >= 3 and "wireless" in parts[2]:
                    name, uuid = parts[0], parts[1]
                    # Also fetch SSID for accuracy
                    ssid_res = subprocess.run(
                        ["nmcli", "-s", "-g", "802-11-wireless.ssid", "connection", "show", uuid],
                        capture_output=True,
                        text=True,
                        timeout=2,
                        check=False
                    )
                    ssid_val = ssid_res.stdout.strip() or name
                    profiles.append({
                        "name": name,
                        "uuid": uuid,
                        "ssid": ssid_val,
                        "type": parts[2],
                        "active": bool(len(parts) > 3 and parts[3])
                    })
            return profiles
        except Exception as e:
            logger.error(f"Error fetching saved Wi-Fi profiles: {e}")
            return []

    def trace_wifi_password(self, target_ssid: str, target_bssid: Optional[str] = None) -> Dict[str, Any]:
        """
        Checks whether the selected network's credentials exist in local NetworkManager profiles.
        Matches by SSID (and BSSID if applicable).
        Never transmits credentials externally.
        """
        target_clean = target_ssid.strip()
        logger.info(f"Tracing password for SSID '{target_clean}' in local NetworkManager profiles...")

        # 1. Quick direct query check by exact name
        try:
            res = subprocess.run(
                ["nmcli", "-s", "-g", "802-11-wireless-security.psk", "connection", "show", target_clean],
                capture_output=True,
                text=True,
                timeout=3,
                check=False
            )
            psk = res.stdout.strip()
            if res.returncode == 0 and psk:
                return {
                    "found": True,
                    "ssid": target_clean,
                    "bssid": target_bssid,
                    "password": psk,
                    "profile_name": target_clean,
                    "source": "Local NetworkManager Profile",
                    "security_type": "WPA/WPA2-PSK",
                    "message": f"Successfully recovered password for '{target_clean}' from local system connection profile."
                }
        except Exception as e:
            logger.debug(f"Direct connection show check failed: {e}")

        # 2. Iterate through all saved wireless profiles to match by 802-11-wireless.ssid
        profiles = self.get_saved_profiles()
        for p in profiles:
            p_name = p["name"]
            p_uuid = p["uuid"]
            p_ssid = p.get("ssid", "")

            # Match criteria: exact match or case-insensitive match
            if (p_name.lower() == target_clean.lower()) or (p_ssid.lower() == target_clean.lower()):
                try:
                    res_psk = subprocess.run(
                        ["nmcli", "-s", "-g", "802-11-wireless-security.psk", "connection", "show", p_uuid],
                        capture_output=True,
                        text=True,
                        timeout=3,
                        check=False
                    )
                    psk = res_psk.stdout.strip()
                    if res_psk.returncode == 0 and psk:
                        return {
                            "found": True,
                            "ssid": target_clean,
                            "bssid": target_bssid,
                            "password": psk,
                            "profile_name": p_name,
                            "uuid": p_uuid,
                            "source": "Local NetworkManager Profile",
                            "security_type": "WPA/WPA2-PSK",
                            "message": f"Successfully recovered password for '{target_clean}' from local connection profile '{p_name}'."
                        }
                except Exception as e:
                    logger.debug(f"Error checking PSK for profile {p_name}: {e}")

        # 3. Not found in local saved profiles
        return {
            "found": False,
            "ssid": target_clean,
            "bssid": target_bssid,
            "password": None,
            "source": None,
            "security_type": None,
            "message": "Password not found in local saved Wi-Fi profiles.",
            "explanation": (
                f"This Ubuntu machine has not previously connected to or saved credentials for '{target_clean}'. "
                "Passive Wi-Fi scanning detects over-the-air beacon broadcasts (SSID, BSSID, channel, and encryption type) "
                "but cannot reveal WPA/WPA2 pre-shared keys, as keys are never broadcast over the air. "
                "To recover access, please check devices previously connected (such as phones or other laptops), "
                "consult the router label/documentation, or refer to the hardware Recovery Assistant."
            )
        }
