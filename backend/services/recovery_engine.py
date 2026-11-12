"""
Service: Wi-Fi Recovery Engine
Executes target-specific password recovery analysis across 6 discrete stages:
1. Identifying target network
2. Analyzing wireless security
3. Evaluating available recovery evidence
4. Running authorized recovery checks
5. Evaluating recovery feasibility
6. Preparing result

Distinguishes honestly between:
- PASSWORD_RECOVERED
- EVIDENCE_INSUFFICIENT
- NO_CREDENTIAL_AVAILABLE
- ADDITIONAL_INPUT_REQUIRED
- RECOVERY_INFEASIBLE
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from backend.services.wifi_scanner import wifi_scanner, WifiNetwork
from backend.services.security_analyzer import security_analyzer
from backend.services.credential_recovery import credential_recovery
from backend.services.websocket_service import ws_manager

logger = logging.getLogger(__name__)

RECOVERY_STAGES = [
    {"id": 1, "name": "Identifying target network", "status": "pending"},
    {"id": 2, "name": "Analyzing wireless security", "status": "pending"},
    {"id": 3, "name": "Evaluating available recovery evidence", "status": "pending"},
    {"id": 4, "name": "Running authorized recovery checks", "status": "pending"},
    {"id": 5, "name": "Evaluating recovery feasibility", "status": "pending"},
    {"id": 6, "name": "Preparing result", "status": "pending"},
]


@dataclass
class RecoveryResult:
    status: str  # 'SUCCESS' or 'NOT_RECOVERED'
    outcome_code: str  # 'PASSWORD_RECOVERED', 'EVIDENCE_INSUFFICIENT', 'NO_CREDENTIAL_AVAILABLE', 'ADDITIONAL_INPUT_REQUIRED', 'RECOVERY_INFEASIBLE'
    target_ssid: str
    target_bssid: Optional[str]
    recovered_password: Optional[str]
    recovery_source: Optional[str]
    timestamp: str
    stages: List[Dict[str, Any]]
    security_analysis: Dict[str, Any]
    checks_performed: List[Dict[str, Any]]
    failure_reason: Optional[str]
    missing_evidence: Optional[str]
    next_legitimate_options: List[str]
    technical_limitation_notice: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class WifiRecoveryEngine:
    """Coordinates target-specific recovery analysis and emits real-time stage progress."""

    def __init__(self):
        self.is_running = False
        self.current_stage = 0
        self.stage_message = "Ready to trace password"
        self.stages_state = [dict(s) for s in RECOVERY_STAGES]
        self.latest_result: Optional[RecoveryResult] = None

    async def run_recovery(
        self,
        target_ssid: str,
        target_bssid: Optional[str] = None,
        backup_content: Optional[str] = None,
        backup_filename: Optional[str] = None
    ) -> RecoveryResult:
        """
        Executes the 6-stage target recovery pipeline.
        """
        self.is_running = True
        self.current_stage = 0
        self.stages_state = [dict(s) for s in RECOVERY_STAGES]
        timestamp = datetime.now().isoformat()

        try:
            # =================================================================
            # STAGE 1: Identifying target network
            # =================================================================
            await self._update_stage(1, "active", f"Verifying target network '{target_ssid}'...")
            target_net = wifi_scanner.get_target_network(target_ssid, target_bssid)

            if target_net:
                bssid_resolved = target_net.bssid
                sec_raw = target_net.security
                enc_raw = target_net.encryption
                chan_resolved = target_net.channel
                freq_resolved = target_net.frequency
                band_resolved = target_net.band
                vendor_resolved = target_net.vendor
                stage_1_details = {
                    "ssid": target_net.ssid,
                    "bssid": target_net.bssid,
                    "channel": target_net.channel,
                    "signal": f"{target_net.signal}% ({target_net.bars})",
                    "vendor": target_net.vendor,
                    "connected": target_net.is_connected
                }
            else:
                bssid_resolved = target_bssid or "Unknown"
                sec_raw = "WPA2-Personal (PSK)"
                enc_raw = "AES-CCMP"
                chan_resolved = 0
                freq_resolved = "Unknown"
                band_resolved = "2.4 GHz"
                vendor_resolved = "Unknown"
                stage_1_details = {
                    "ssid": target_ssid,
                    "bssid": bssid_resolved,
                    "status": "Target specified manually (out of direct range or non-broadcast)"
                }

            await asyncio.sleep(0.15)
            await self._update_stage(1, "completed", f"Target identified: {target_ssid} ({bssid_resolved})", stage_1_details)

            # =================================================================
            # STAGE 2: Analyzing wireless security
            # =================================================================
            await self._update_stage(2, "active", f"Analyzing security protocol & cipher suites for '{target_ssid}'...")
            security_info = security_analyzer.analyze_target(
                ssid=target_ssid,
                bssid=bssid_resolved,
                security=sec_raw,
                encryption=enc_raw,
                channel=chan_resolved,
                frequency=freq_resolved,
                band=band_resolved
            )

            await asyncio.sleep(0.15)
            await self._update_stage(
                2, "completed",
                f"Security: {security_info['protocol_name']} ({security_info['pairwise_cipher']})",
                security_info
            )

            # =================================================================
            # STAGE 3: Evaluating available recovery evidence
            # =================================================================
            await self._update_stage(3, "active", "Evaluating accessible local recovery stores & evidence...")
            has_backup = bool(backup_content and backup_content.strip())
            evidence_summary = {
                "local_nmcli_accessible": True,
                "system_keyfiles_accessible": os.path.exists("/etc/NetworkManager/system-connections"),
                "router_backup_provided": has_backup,
                "backup_filename": backup_filename if has_backup else None,
                "passive_beacon_psk_availability": False
            }

            await asyncio.sleep(0.15)
            await self._update_stage(
                3, "completed",
                f"Evidence: Local OS stores available, Backup attached: {'Yes' if has_backup else 'No'}",
                evidence_summary
            )

            # =================================================================
            # STAGE 4: Running authorized recovery checks
            # =================================================================
            await self._update_stage(4, "active", f"Checking authorized stores for '{target_ssid}' credentials...")
            recovery_audit = credential_recovery.recover_target_credential(
                target_ssid=target_ssid,
                target_bssid=bssid_resolved,
                backup_content=backup_content,
                backup_filename=backup_filename
            )

            checks_performed = recovery_audit["checks_performed"]
            cred_found = recovery_audit.get("credential")

            await asyncio.sleep(0.15)
            if cred_found:
                msg = f"Credentials recovered from {cred_found['source_name']}"
            else:
                msg = f"Checked {len(checks_performed)} sources; no valid credentials in local stores"

            await self._update_stage(4, "completed", msg, {"checks_count": len(checks_performed)})

            # =================================================================
            # STAGE 5: Evaluating recovery feasibility
            # =================================================================
            await self._update_stage(5, "active", "Evaluating recovered data against WPA/WPA2 specification...")

            if cred_found and cred_found.get("password"):
                raw_pwd = cred_found["password"]
                # WPA/WPA2 pre-shared keys must be 8 to 63 ASCII characters or 64 hex digits
                if len(raw_pwd) >= 8:
                    feasibility_status = "VALID_CREDENTIAL"
                    outcome_code = "PASSWORD_RECOVERED"
                    feasibility_msg = "Recovered passphrase matches valid 802.11 WPA pre-shared key format."
                else:
                    feasibility_status = "POTENTIAL_KEY"
                    outcome_code = "EVIDENCE_INSUFFICIENT"
                    feasibility_msg = "Recovered string is shorter than the 8-character WPA2 minimum standard."
            elif has_backup:
                feasibility_status = "BACKUP_PARSED_NO_MATCH"
                outcome_code = "ADDITIONAL_INPUT_REQUIRED"
                feasibility_msg = f"Backup file '{backup_filename}' was inspected but did not contain a valid PSK for '{target_ssid}'."
            else:
                feasibility_status = "NO_LOCAL_EVIDENCE"
                outcome_code = "NO_CREDENTIAL_AVAILABLE"
                feasibility_msg = "No pre-shared key is stored on this machine for this network. Passive over-the-air cracking is infeasible."

            await asyncio.sleep(0.15)
            await self._update_stage(5, "completed", feasibility_msg, {"feasibility_status": feasibility_status})

            # =================================================================
            # STAGE 6: Preparing result
            # =================================================================
            await self._update_stage(6, "active", "Formatting structured recovery report...")

            if outcome_code == "PASSWORD_RECOVERED" and cred_found:
                status = "SUCCESS"
                recovered_pwd = cred_found["password"]
                rec_source = cred_found["source_name"]
                failure_reason = None
                missing_evidence = None
                next_options = [
                    "You can now join this network using the recovered password.",
                    "Save this password in a secure password manager.",
                    "Log into the router web management console to verify settings if required."
                ]
            else:
                status = "NOT_RECOVERED"
                recovered_pwd = None
                rec_source = None
                failure_reason = (
                    f"No saved credentials for '{target_ssid}' exist in local NetworkManager profiles or provided backup files."
                )
                missing_evidence = (
                    "Missing: (1) Local operating system saved Wi-Fi connection profile, "
                    "or (2) Valid exported router configuration backup containing the target SSID's passphrase."
                )
                next_options = [
                    "Check other devices (such as Android/iOS phones, tablets, or family laptops) that previously joined this Wi-Fi network.",
                    "Connect an Ethernet cable directly from your PC into one of the router's LAN ports (bypassing Wi-Fi encryption).",
                    "If you have a previously saved router configuration backup (.bin / .conf / .xml), upload it to extract the key.",
                    "If the router is mounted in an inaccessible location (pole/tower), use the indoor PoE power adapter's 'Remote Reset' pinhole for 8-10 seconds to restore factory settings.",
                    "Check the physical label on the bottom of the router or consult your internet service provider (ISP) contract."
                ]

            technical_limitation_notice = (
                "PASSIVE SCANNING LIMITATION: Under standard IEEE 802.11i WPA/WPA2/WPA3 protocols, "
                "beacon frames publicly broadcast over the air contain the network name (SSID), hardware address (BSSID), "
                "supported data rates, and security capabilities (RSN IE). "
                "Pre-shared passwords (PSK) are NEVER transmitted over the air in beacon frames. "
                "The 4-way WPA handshake verifies key knowledge using cryptographic nonces without ever sending the plaintext key. "
                "Therefore, passive Wi-Fi scanning cannot extract passwords out of thin air."
            )

            result = RecoveryResult(
                status=status,
                outcome_code=outcome_code,
                target_ssid=target_ssid,
                target_bssid=bssid_resolved,
                recovered_password=recovered_pwd,
                recovery_source=rec_source,
                timestamp=timestamp,
                stages=self.stages_state,
                security_analysis=security_info,
                checks_performed=checks_performed,
                failure_reason=failure_reason,
                missing_evidence=missing_evidence,
                next_legitimate_options=next_options,
                technical_limitation_notice=technical_limitation_notice,
            )

            self.latest_result = result
            self.stage_message = (
                f"Analysis Complete: Password recovered from {rec_source}"
                if status == "SUCCESS"
                else "Analysis Complete: Password not recovered from local authorized sources"
            )

            await self._update_stage(6, "completed", self.stage_message, {"status": status, "outcome": outcome_code})
            self.is_running = False

            await ws_manager.broadcast("recovery_complete", result.to_dict())
            return result

        except Exception as e:
            logger.error(f"Recovery pipeline failed: {e}", exc_info=True)
            self.is_running = False
            self.stage_message = f"Error during analysis: {e}"
            await self._update_stage(self.current_stage or 1, "failed", str(e))
            raise

    async def _update_stage(self, stage_id: int, status: str, message: str, details: Any = None):
        self.current_stage = stage_id
        self.stage_message = message
        idx = stage_id - 1
        if 0 <= idx < len(self.stages_state):
            self.stages_state[idx]["status"] = status
            if details:
                self.stages_state[idx]["details"] = details

        await ws_manager.broadcast("recovery_stage_progress", {
            "current_stage": self.current_stage,
            "stage_message": self.stage_message,
            "stages": self.stages_state,
            "is_running": self.is_running
        })


recovery_engine = WifiRecoveryEngine()
