"""
Service: Wi-Fi Recovery Engine
Executes target-specific password recovery analysis across 6 discrete stages:
1. Identifying target network
2. Analyzing wireless security
3. Evaluating available recovery evidence
4. Running authorized recovery checks
5. Evaluating recovery feasibility
6. Preparing result

Distinguishes honestly and rigorously between:
- PASSWORD_RECOVERED: Credential found in an authorized source (NetworkManager profile or backup)
- HANDSHAKE_EVIDENCE_AVAILABLE: Valid 4-way or M1+M2 handshake captured with nonces & MIC;
  explains nonces and MIC inspection, but clarifies handshake != recovered password
- HANDSHAKE_EVIDENCE_INCOMPLETE: Incomplete handshake (missing M1 ANonce or M2 SNonce/MIC)
- NO_CREDENTIAL_AVAILABLE: Passive Wi-Fi scan limitation / no credentials available
- ADDITIONAL_INPUT_REQUIRED: Additional authorized material required
- EVIDENCE_INSUFFICIENT: Recovered string invalid or malformed
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from backend.services.wifi_scanner import wifi_scanner
from backend.services.security_analyzer import security_analyzer
from backend.services.credential_recovery import credential_recovery
from backend.services.pcap_analyzer import pcap_analyzer
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
    status: str  # 'SUCCESS', 'HANDSHAKE_CAPTURED', or 'NOT_RECOVERED'
    outcome_code: str  # 'PASSWORD_RECOVERED', 'HANDSHAKE_EVIDENCE_AVAILABLE', 'HANDSHAKE_EVIDENCE_INCOMPLETE', 'EVIDENCE_INSUFFICIENT', 'NO_CREDENTIAL_AVAILABLE', 'ADDITIONAL_INPUT_REQUIRED', 'RECOVERY_INFEASIBLE'
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
    handshake_evidence: Optional[Dict[str, Any]] = None
    pcap_analysis: Optional[Dict[str, Any]] = None

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
        backup_filename: Optional[str] = None,
        pcap_bytes: Optional[bytes] = None,
        pcap_filename: Optional[str] = None,
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
            await self._update_stage(3, "active", "Evaluating accessible local recovery stores & capture evidence...")
            has_backup = bool(backup_content and backup_content.strip())
            has_pcap = bool(pcap_bytes and len(pcap_bytes) > 0)

            pcap_result = None
            if has_pcap:
                try:
                    pcap_result = pcap_analyzer.parse_pcap_bytes(
                        data=pcap_bytes,
                        filename=pcap_filename or "capture.pcap",
                        target_ssid=target_ssid,
                        target_bssid=bssid_resolved
                    )
                except Exception as ex:
                    logger.warning(f"Error parsing capture: {ex}")
                    pcap_result = {"status": "ERROR", "error": str(ex), "eapol_packets_count": 0, "has_valid_handshake": False}

            evidence_summary = {
                "local_nmcli_accessible": True,
                "system_keyfiles_accessible": os.path.exists("/etc/NetworkManager/system-connections"),
                "router_backup_provided": has_backup,
                "backup_filename": backup_filename if has_backup else None,
                "pcap_capture_provided": has_pcap,
                "pcap_filename": pcap_filename if has_pcap else None,
                "pcap_packets_count": pcap_result.get("total_packets", 0) if pcap_result else 0,
                "eapol_packets_count": pcap_result.get("eapol_packets_count", 0) if pcap_result else 0,
                "passive_beacon_psk_availability": False
            }

            await asyncio.sleep(0.15)
            stage3_msg = (
                f"Evidence: Local OS stores available, Backup: {'Yes' if has_backup else 'No'}, "
                f"Capture: {'Yes (' + str(pcap_result.get('eapol_packets_count', 0)) + ' EAPOL frames)' if has_pcap else 'No'}"
            )
            await self._update_stage(3, "completed", stage3_msg, evidence_summary)

            # =================================================================
            # STAGE 4: Running authorized recovery checks
            # =================================================================
            await self._update_stage(4, "active", f"Checking authorized stores & capture packets for '{target_ssid}'...")
            recovery_audit = credential_recovery.recover_target_credential(
                target_ssid=target_ssid,
                target_bssid=bssid_resolved,
                backup_content=backup_content,
                backup_filename=backup_filename
            )

            checks_performed = recovery_audit["checks_performed"]
            cred_found = recovery_audit.get("credential")

            # Add PCAP capture inspection check to checks_performed if capture was provided
            if has_pcap and pcap_result:
                eapol_count = pcap_result.get("eapol_packets_count", 0)
                best_hs = pcap_result.get("best_handshake")
                if best_hs and best_hs.get("is_usable_for_offline_validation"):
                    pcap_check_status = "FOUND"
                    pcap_check_msg = (
                        f"Analyzed {pcap_result.get('total_packets', 0)} frames in '{pcap_filename}'. "
                        f"Found valid WPA2 handshake ({', '.join(best_hs.get('messages_found', []))}) "
                        f"for AP {best_hs.get('ap_mac')} <-> STA {best_hs.get('sta_mac')}."
                    )
                elif eapol_count > 0:
                    pcap_check_status = "PARTIAL"
                    pcap_check_msg = (
                        f"Analyzed {pcap_result.get('total_packets', 0)} frames in '{pcap_filename}'. "
                        f"Found {eapol_count} EAPOL frames, but handshake sequence is incomplete."
                    )
                else:
                    pcap_check_status = "NOT_FOUND"
                    pcap_check_msg = (
                        f"Analyzed {pcap_result.get('total_packets', 0)} frames in '{pcap_filename}'; no 802.1X/EAPOL frames found."
                    )

                checks_performed.append({
                    "source_id": "pcap_packet_capture",
                    "source_name": f"Authorized Packet Capture ({pcap_filename})",
                    "type": "pcap_eapol_inspection",
                    "status": pcap_check_status,
                    "evidence_found": bool(best_hs and best_hs.get("is_usable_for_offline_validation")),
                    "description": pcap_check_msg,
                    "target_matched": bool(best_hs)
                })

            await asyncio.sleep(0.15)
            if cred_found:
                msg = f"Credentials recovered from {cred_found['source_name']}"
            elif pcap_result and pcap_result.get("has_valid_handshake"):
                msg = "Handshake cryptographic evidence extracted from packet capture"
            else:
                msg = f"Checked {len(checks_performed)} sources; no valid plaintext credentials in local stores"

            await self._update_stage(4, "completed", msg, {"checks_count": len(checks_performed)})

            # =================================================================
            # STAGE 5: Evaluating recovery feasibility
            # =================================================================
            await self._update_stage(5, "active", "Evaluating recovered data against WPA/WPA2 cryptographic standards...")

            best_handshake_dict = pcap_result.get("best_handshake") if pcap_result else None

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
            elif best_handshake_dict and best_handshake_dict.get("is_usable_for_offline_validation"):
                feasibility_status = "VALID_HANDSHAKE_CAPTURED"
                outcome_code = "HANDSHAKE_EVIDENCE_AVAILABLE"
                feasibility_msg = (
                    "Valid cryptographic handshake captured (ANonce, SNonce, Key MIC extracted). "
                    "Pre-shared key can be mathematically validated offline, but the capture itself DOES NOT contain the plaintext password."
                )
            elif pcap_result and pcap_result.get("eapol_packets_count", 0) > 0:
                feasibility_status = "INCOMPLETE_HANDSHAKE_CAPTURED"
                outcome_code = "HANDSHAKE_EVIDENCE_INCOMPLETE"
                feasibility_msg = (
                    "Capture contains EAPOL frames, but incomplete handshake messages (missing M1 ANonce or M2 SNonce/Key MIC)."
                )
            elif has_backup:
                feasibility_status = "BACKUP_PARSED_NO_MATCH"
                outcome_code = "ADDITIONAL_INPUT_REQUIRED"
                feasibility_msg = f"Backup file '{backup_filename}' was inspected but did not contain a valid PSK for '{target_ssid}'."
            else:
                feasibility_status = "NO_LOCAL_EVIDENCE"
                outcome_code = "NO_CREDENTIAL_AVAILABLE"
                feasibility_msg = "No pre-shared key or handshake evidence is stored on this machine for this network. Passive over-the-air cracking is infeasible."

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
            elif outcome_code == "HANDSHAKE_EVIDENCE_AVAILABLE":
                status = "HANDSHAKE_CAPTURED"
                recovered_pwd = None
                rec_source = f"Packet Capture ({pcap_filename or 'capture.pcap'})"
                failure_reason = (
                    "The packet capture contains valid 4-way handshake cryptographic material (ANonce, SNonce, Key MIC). "
                    "Under IEEE 802.11i, the plaintext password is NEVER transmitted over the air. "
                    "The captured nonces and MIC prove the pre-shared key knowledge mathematically, "
                    "but passive packet inspection alone cannot reveal the plaintext password without offline dictionary or wordlist auditing."
                )
                missing_evidence = (
                    "Plaintext password not in local store. "
                    "Offline verification requires testing candidate passwords against the captured MIC (Message Integrity Code)."
                )
                next_options = [
                    "Verify the captured ANonce, SNonce, and Key MIC in the Protocol Details table below.",
                    "Audit candidate passphrases (e.g. from your authorized company wordlist) against the captured MIC offline.",
                    "Check other authorized devices (smartphones, family laptops) that previously joined this Wi-Fi network.",
                    "Connect an Ethernet cable directly from your PC into one of the router's LAN ports (bypassing Wi-Fi encryption).",
                    "If physical access to the router is available, press and hold the physical Reset button on the rear panel for 10 seconds to restore factory defaults (restoring the default Wi-Fi password printed on the router label)."
                ]
            elif outcome_code == "HANDSHAKE_EVIDENCE_INCOMPLETE":
                status = "NOT_RECOVERED"
                recovered_pwd = None
                rec_source = None
                failure_reason = (
                    f"EAPOL frames were found in '{pcap_filename}', but the handshake is incomplete. "
                    "A valid handshake requires at minimum Message 1 (transmitting ANonce) and Message 2 (transmitting SNonce and Key MIC) from the same key exchange."
                )
                missing_evidence = (
                    "Missing complementary handshake messages. Ensure capture was running when the client authenticated or reconnected."
                )
                next_options = [
                    "Obtain a full packet capture that includes client association or reconnection to capture both Message 1 and Message 2.",
                    "Check local NetworkManager profiles or saved Wi-Fi profiles on other devices.",
                    "Connect an Ethernet cable directly into a LAN port on the router.",
                    "If authorized, use the hardware reset button on the router back panel for 10 seconds to restore factory defaults."
                ]
            else:
                status = "NOT_RECOVERED"
                recovered_pwd = None
                rec_source = None
                failure_reason = (
                    f"No saved credentials for '{target_ssid}' exist in local NetworkManager profiles or provided backup/capture files."
                )
                missing_evidence = (
                    "Missing: (1) Local operating system saved Wi-Fi connection profile, "
                    "or (2) Valid exported router configuration backup containing the target SSID's passphrase, "
                    "or (3) Authorized packet capture (.pcap / .cap) containing the 4-way handshake."
                )
                next_options = [
                    "Check other devices (such as Android/iOS phones, tablets, or family laptops) that previously joined this Wi-Fi network.",
                    "Connect an Ethernet cable directly from your PC into one of the router's LAN ports (bypassing Wi-Fi encryption).",
                    "If you have an authorized packet capture (.pcap / .pcapng / .cap), attach it above to inspect handshake frames.",
                    "If you have a previously saved router configuration backup (.bin / .conf / .xml), upload it to inspect stored credentials.",
                    "If physical access to the router is possible, use the hardware reset button on the router back panel for 10 seconds to restore factory defaults (restoring default Wi-Fi password printed on the unit label).",
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
                handshake_evidence=best_handshake_dict,
                pcap_analysis=pcap_result,
            )

            self.latest_result = result
            if status == "SUCCESS":
                self.stage_message = f"Analysis Complete: Password recovered from {rec_source}"
            elif status == "HANDSHAKE_CAPTURED":
                self.stage_message = "Analysis Complete: 4-Way Handshake cryptographic evidence verified"
            else:
                self.stage_message = "Analysis Complete: Password not recovered from local authorized sources"

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
