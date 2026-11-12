"""
Module: Recovery Decision Engine
Analyzes all collected discovery evidence (network topology, gateway reachability,
vendor identification, management interface status, and local credentials)
to generate a concrete, actionable, evidence-based recovery plan across Scenarios 1 to 5.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict


@dataclass
class RecoveryPlan:
    scenario_id: str
    scenario_title: str
    headline: str
    summary: str
    confidence_rating: str = "High"
    confirmed_facts: List[str] = field(default_factory=list)
    unknowns: List[str] = field(default_factory=list)
    obstacles: List[str] = field(default_factory=list)
    working_hypotheses: List[str] = field(default_factory=list)
    unknown_variables: List[str] = field(default_factory=list)
    recommended_action: str = ""
    action_steps: List[Any] = field(default_factory=list)
    technical_notes: List[str] = field(default_factory=list)
    hardware_reset_guide: Optional[Dict[str, Any]] = None
    model_specific_reset: Optional[Dict[str, Any]] = None
    poe_remote_reset_guide: Optional[Dict[str, Any]] = None
    isp_pppoe_warning: str = ""
    official_vendor_docs: List[Dict[str, str]] = field(default_factory=list)
    documentation_links: List[Dict[str, str]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    scenario_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["scenario_summary"] = self.summary
        d["working_hypotheses"] = self.working_hypotheses or self.obstacles
        d["unknown_variables"] = self.unknown_variables or self.unknowns
        d["official_vendor_docs"] = self.official_vendor_docs or self.documentation_links
        return d


class RecoveryDecisionEngine:
    """Synthesizes diagnostic evidence into a concrete recovery plan across 5 scenarios."""

    @classmethod
    def evaluate(
        cls,
        has_network_connection: bool,
        connection_type: str,  # 'wifi', 'ethernet', 'none'
        gateway_ip: Optional[str],
        gateway_mac: Optional[str],
        detected_vendor: str,
        is_tplink_candidate: bool,
        model_hint: Optional[str],
        management_endpoints: List[Dict[str, Any]],
        credential_sources: List[Dict[str, Any]],
        nearby_ssids: List[str],
        active_interface_name: Optional[str],
    ) -> RecoveryPlan:
        confirmed_facts: List[str] = []
        unknowns: List[str] = []
        obstacles: List[str] = []
        working_hypotheses: List[str] = []
        warnings: List[str] = []
        technical_notes: List[str] = []
        doc_links: List[Dict[str, str]] = []

        has_management_page = any(
            ep.get("status_code", 0) in (200, 301, 302, 401) for ep in management_endpoints
        )
        best_mgmt_url = next(
            (
                ep.get("final_url") or ep.get("url")
                for ep in management_endpoints
                if ep.get("status_code", 0) in (200, 301, 302, 401)
            ),
            None,
        )

        has_saved_credential = any(
            cs.get("status") == "Found" or cs.get("matching_credential_found") is True
            for cs in credential_sources
        )
        is_ethernet = (connection_type == "ethernet")

        # 1. Compile Confirmed Facts
        if gateway_ip:
            confirmed_facts.append(f"Default Gateway discovered at IPv4 address: {gateway_ip}")
        if gateway_mac:
            confirmed_facts.append(f"Gateway hardware MAC address: {gateway_mac} (Vendor: {detected_vendor})")
        if has_management_page and best_mgmt_url:
            confirmed_facts.append(f"Router web management interface is reachable at: {best_mgmt_url}")
        if model_hint:
            confirmed_facts.append(f"Hardware model signature detected: {model_hint}")
        if is_ethernet:
            confirmed_facts.append("Direct wired Ethernet link established with local network switch/router.")
        elif connection_type == "wifi":
            confirmed_facts.append("System is connected via wireless Wi-Fi link.")

        # 2. Compile Unknowns & Hypotheses
        if not has_saved_credential:
            unknowns.append("Wi-Fi pre-shared key (PSK) is not stored in local operating system profiles.")
        if not model_hint and is_tplink_candidate:
            working_hypotheses.append("Target router is likely a TP-Link SOHO router based on MAC OUI resolution.")
        unknowns.append("Current administrator web portal password is unknown.")
        unknowns.append("ISP connection parameters (PPPoE credentials, VLAN tags) are unknown unless documented on contract.")

        # Vendor Documentation references
        if "TP-LINK" in detected_vendor.upper() or is_tplink_candidate:
            doc_links.append({"title": "Official TP-Link Password Recovery Guide", "url": "https://www.tp-link.com/en/support/faq/73/"})
            doc_links.append({"title": "TP-Link Factory Reset Instructions", "url": "https://www.tp-link.com/en/support/faq/497/"})
            doc_links.append({"title": "TP-Link Tether Mobile App Recovery", "url": "https://www.tp-link.com/en/tether/"})
        elif "ZTE" in detected_vendor.upper():
            doc_links.append({"title": "ZTE GPON ONT Web Management Guide", "url": "https://www.ztedevices.com"})
        elif "HUAWEI" in detected_vendor.upper():
            doc_links.append({"title": "Huawei Optical Terminal Access Guide", "url": "https://support.huawei.com"})
        elif "ASUS" in detected_vendor.upper():
            doc_links.append({"title": "ASUS Router Hard Reset & Rescue Guide", "url": "https://www.asus.com/support"})

        critical_isp_warning = (
            "CRITICAL WARNING: Performing a factory reset will permanently erase all custom configurations, "
            "including PPPoE internet usernames/passwords, ISP VLAN tags (e.g. VLAN 35 for Viettel/VNPT/FPT), "
            "custom subnet ranges, and port forwarding rules. Ensure you have your ISP internet contract details before resetting."
        )

        poe_guide = {
            "applicable": True,
            "indoor_unit": "TP-Link Passive PoE Injector (24V / 48V indoor adapter)",
            "method": (
                "For outdoor or pole-mounted routers (such as PharOS CPE210/CPE510, EAP Outdoor): "
                "Do NOT climb the pole. Locate the indoor PoE injector power adapter. "
                "Locate the 'Remote Reset' pinhole button on the indoor PoE unit. "
                "Use a paperclip to press and hold the Remote Reset button for 8-10 seconds while powered on to factory reset from ground level."
            ),
            "note": "Avoid climbing hazardous poles or outdoor towers."
        }

        hardware_guide = cls._build_hardware_guide(model_hint, is_tplink_candidate)
        model_reset = {
            "model": model_hint or "TP-Link Standard SOHO",
            "hold_duration_sec": 8,
            "led_indicator": "SYS LED flashes rapidly, then all LEDs turn on during reboot cycle.",
            "default_ip": "192.168.0.1",
            "default_web_url": "http://tplinkwifi.net",
            "default_credentials": "admin / admin (or prompt to create new password)"
        }

        technical_notes.append("Passive Wi-Fi scanning cannot crack or extract WPA2 pre-shared keys.")
        technical_notes.append("Layer 2 Ethernet connection bypasses wireless authentication barriers.")

        # =====================================================================
        # SCENARIO 1: Management Page Reachable with Discovered Credentials
        # =====================================================================
        if has_management_page and best_mgmt_url and has_saved_credential:
            scenario_id = "scenario_1"
            scenario_title = "Scenario 1: Router Web Management Page is Directly Reachable"
            headline = f"Admin Portal Located at {best_mgmt_url}"
            summary = (
                f"The router's web management interface was successfully located and responded at {best_mgmt_url}. "
                "Saved local connection credentials were recovered from system stores."
            )
            obstacles.append("Web administration login requires valid administrator credentials.")
            action_steps = [
                {
                    "step": 1,
                    "title": "Open Router Web Management",
                    "instruction": f"Navigate to the router portal in your web browser: {best_mgmt_url}",
                    "command": None,
                    "caution": None,
                },
                {
                    "step": 2,
                    "title": "Apply Discovered Credentials",
                    "instruction": "Test discovered local credentials or try default administrator credentials (admin/admin).",
                    "command": None,
                    "caution": "Do not attempt brute force scripts; routers enforce rate-limiting lockout.",
                },
                {
                    "step": 3,
                    "title": "TP-Link Cloud / Tether App",
                    "instruction": "If linked to a TP-Link ID, use the 'Forgot Password?' prompt or the TP-Link Tether mobile app.",
                    "command": None,
                    "caution": None,
                }
            ]

            return RecoveryPlan(
                scenario_id=scenario_id,
                scenario_title=scenario_title,
                headline=headline,
                summary=summary,
                confidence_rating="High",
                confirmed_facts=confirmed_facts,
                unknowns=unknowns,
                obstacles=obstacles,
                working_hypotheses=working_hypotheses,
                unknown_variables=unknowns,
                recommended_action="Access management portal and test recovered credentials.",
                action_steps=action_steps,
                technical_notes=technical_notes,
                hardware_reset_guide=hardware_guide,
                model_specific_reset=model_reset,
                poe_remote_reset_guide=poe_guide,
                isp_pppoe_warning=critical_isp_warning,
                official_vendor_docs=doc_links,
                documentation_links=doc_links,
                warnings=warnings,
                scenario_summary=summary,
            )

        # =====================================================================
        # SCENARIO 4: Router Reachable but Admin Credentials Unknown
        # =====================================================================
        if (has_management_page and best_mgmt_url) or (gateway_ip and is_tplink_candidate and not has_saved_credential and not is_ethernet):
            scenario_id = "scenario_4"
            scenario_title = "Scenario 4: Router Reachable but Admin Credentials Unknown"
            headline = f"Router Identified ({detected_vendor}), Authentication Required"
            summary = (
                f"The router is reachable at {best_mgmt_url or gateway_ip}. "
                "No valid administrator credentials exist in local stores. Factory reset is the authorized standard."
            )
            obstacles.append("No saved credentials found in local NetworkManager profiles or user backups.")
            action_steps = [
                {
                    "step": 1,
                    "title": "Check Physical Label & ISP Contract",
                    "instruction": "Check the underside label of the router or your ISP contract document for default credentials.",
                    "command": None,
                    "caution": None,
                },
                {
                    "step": 2,
                    "title": "Backup ISP PPPoE Credentials",
                    "instruction": "Locate your ISP PPPoE username and password before resetting.",
                    "command": None,
                    "caution": "Resetting without PPPoE credentials will disrupt internet access.",
                },
                {
                    "step": 3,
                    "title": "Hardware Factory Reset",
                    "instruction": f"Press and hold the physical Reset button on {model_hint or 'the router'} for 8-10 seconds.",
                    "command": None,
                    "caution": None,
                }
            ]

            return RecoveryPlan(
                scenario_id=scenario_id,
                scenario_title=scenario_title,
                headline=headline,
                summary=summary,
                confidence_rating="High",
                confirmed_facts=confirmed_facts,
                unknowns=unknowns,
                obstacles=obstacles,
                working_hypotheses=working_hypotheses,
                unknown_variables=unknowns,
                recommended_action="Perform official hardware reset after verifying ISP connection credentials.",
                action_steps=action_steps,
                technical_notes=technical_notes,
                hardware_reset_guide=hardware_guide,
                model_specific_reset=model_reset,
                poe_remote_reset_guide=poe_guide,
                isp_pppoe_warning=critical_isp_warning,
                official_vendor_docs=doc_links,
                documentation_links=doc_links,
                warnings=warnings,
                scenario_summary=summary,
            )

        # =====================================================================
        # SCENARIO 3: Connected via Wired Ethernet (IP Changed / Unknown)
        # =====================================================================
        if is_ethernet and gateway_ip:
            scenario_id = "scenario_3"
            scenario_title = "Scenario 3: Direct Ethernet Connection Established"
            headline = f"Connected via Ethernet to Gateway {gateway_ip}"
            summary = (
                "Your computer is connected via wired Ethernet. The gateway address was resolved, "
                "bypassing the need for a Wi-Fi password."
            )
            action_steps = [
                {
                    "step": 1,
                    "title": "Verify Gateway Connectivity",
                    "instruction": f"Send ICMP probe to gateway {gateway_ip} to verify link.",
                    "command": f"ping -c 3 {gateway_ip}",
                    "caution": None,
                },
                {
                    "step": 2,
                    "title": "Inspect HTTP & HTTPS Management Ports",
                    "instruction": f"Open http://{gateway_ip} or check non-standard ports (8080, 8443).",
                    "command": f"curl -I http://{gateway_ip}",
                    "caution": None,
                },
                {
                    "step": 3,
                    "title": "Sweep Private Subnet Ranges",
                    "instruction": "If management IP was changed, scan standard subnets (192.168.0.0/24, 192.168.1.0/24, 10.0.0.0/24).",
                    "command": f"sudo dhclient {active_interface_name or 'eth0'}",
                    "caution": None,
                }
            ]

            return RecoveryPlan(
                scenario_id=scenario_id,
                scenario_title=scenario_title,
                headline=headline,
                summary=summary,
                confidence_rating="High",
                confirmed_facts=confirmed_facts,
                unknowns=unknowns,
                obstacles=obstacles,
                working_hypotheses=working_hypotheses,
                unknown_variables=unknowns,
                recommended_action="Access router via local Ethernet IP and review model-specific hardware reset steps.",
                action_steps=action_steps,
                technical_notes=technical_notes,
                hardware_reset_guide=hardware_guide,
                model_specific_reset=model_reset,
                poe_remote_reset_guide=poe_guide,
                isp_pppoe_warning=critical_isp_warning,
                official_vendor_docs=doc_links,
                documentation_links=doc_links,
                warnings=warnings,
                scenario_summary=summary,
            )

        # =====================================================================
        # SCENARIO 2: Not connected over Wi-Fi (No Known Password)
        # =====================================================================
        if (not has_network_connection or not gateway_ip) and nearby_ssids:
            scenario_id = "scenario_2"
            scenario_title = "Scenario 2: Not Connected over Wi-Fi (Password Unknown)"
            headline = "Candidate Wi-Fi Airwaves Detected, Unconnected"
            summary = (
                "Candidate Wi-Fi networks were detected over the air, but the Wi-Fi password is unknown. "
                "Passive over-the-air Wi-Fi scanning detects beacon frames (SSID, BSSID, Channel, Encryption) "
                "but cannot retrieve pre-shared keys, as WPA/WPA2 security keys are never transmitted over the air."
            )
            obstacles.append("Computer cannot communicate with the router without being joined to its local network.")
            obstacles.append("Passive radio sniffing cannot reveal WPA2 pre-shared keys.")

            action_steps = [
                {
                    "step": 1,
                    "title": "Connect Ethernet Cable",
                    "instruction": "Connect an RJ45 Ethernet cable directly from your computer into one of the router's LAN ports (yellow).",
                    "command": None,
                    "caution": None,
                },
                {
                    "step": 2,
                    "title": "Pole-Mounted / Outdoor Router Remote Reset",
                    "instruction": "If the router is on a pole or tower, locate the indoor PoE injector power supply. Use a paperclip to press the 'Remote Reset' button for 8-10 seconds.",
                    "command": None,
                    "caution": "Do not climb hazardous poles.",
                },
                {
                    "step": 3,
                    "title": "Check Other Family Devices",
                    "instruction": "Check previously joined smartphones or laptops that have saved the Wi-Fi network profile.",
                    "command": None,
                    "caution": None,
                }
            ]

            return RecoveryPlan(
                scenario_id=scenario_id,
                scenario_title=scenario_title,
                headline=headline,
                summary=summary,
                confidence_rating="High",
                confirmed_facts=confirmed_facts,
                unknowns=unknowns,
                obstacles=obstacles,
                working_hypotheses=working_hypotheses,
                unknown_variables=unknowns,
                recommended_action="Connect an Ethernet cable directly to the router's LAN port or use the indoor PoE Remote Reset pinhole.",
                action_steps=action_steps,
                technical_notes=technical_notes,
                hardware_reset_guide=hardware_guide,
                model_specific_reset=model_reset,
                poe_remote_reset_guide=poe_guide,
                isp_pppoe_warning=critical_isp_warning,
                official_vendor_docs=doc_links,
                documentation_links=doc_links,
                warnings=warnings,
                scenario_summary=summary,
            )

        # =====================================================================
        # SCENARIO 5: Default Fallback (No Usable Recovery Source)
        # =====================================================================
        scenario_id = "scenario_5"
        scenario_title = "Scenario 5: No Usable Recovery Source or Interface Disconnected"
        headline = "Unable to Resolve Router Architecture"
        summary = (
            "The diagnosis could not detect an active default gateway or reachable management portal. "
            "No nearby wireless signals or active network interfaces were found."
        )
        unknowns.append("No active physical or wireless link detected.")
        action_steps = [
            {
                "step": 1,
                "title": "Connect Network Cable",
                "instruction": "Plug an Ethernet cable from your computer to the router.",
                "command": "ip link show",
                "caution": None,
            },
            {
                "step": 2,
                "title": "Verify Network Interface",
                "instruction": "Ensure your network interface is set to auto DHCP configuration.",
                "command": "sudo ip link set up dev eth0",
                "caution": None,
            }
        ]

        return RecoveryPlan(
            scenario_id=scenario_id,
            scenario_title=scenario_title,
            headline=headline,
            summary=summary,
            confidence_rating="Low",
            confirmed_facts=confirmed_facts,
            unknowns=unknowns,
            obstacles=["No reachable local gateway or active interface route."],
            working_hypotheses=["Network interface may be disabled or cable disconnected."],
            unknown_variables=unknowns,
            recommended_action="Connect an Ethernet cable and verify network interface status.",
            action_steps=action_steps,
            technical_notes=technical_notes,
            hardware_reset_guide=hardware_guide,
            model_specific_reset=model_reset,
            poe_remote_reset_guide=poe_guide,
            isp_pppoe_warning=critical_isp_warning,
            official_vendor_docs=doc_links,
            documentation_links=doc_links,
            warnings=warnings,
            scenario_summary=summary,
        )

    @classmethod
    def _build_hardware_guide(cls, model_hint: Optional[str], is_tplink: bool) -> Dict[str, Any]:
        """Builds accurate model-specific hardware reset instructions."""
        return {
            "vendor": "TP-Link" if is_tplink else "General Router",
            "model_hint": model_hint or "Standard TP-Link SOHO Router",
            "critical_warning": (
                "Factory reset will permanently wipe custom configurations, including PPPoE login credentials, "
                "ISP VLAN IDs, static IP routing, and Wi-Fi security keys. Ensure you possess your ISP account details."
            ),
            "pole_mounted_outdoor_instructions": (
                "IMPORTANT FOR POLE-MOUNTED / INACCESSIBLE OUTDOOR ROUTERS (CPE210 / CPE510 / EAP Outdoor):\n"
                "Do NOT climb the pole! Outdoor TP-Link access points are powered through an indoor PoE Injector adapter. "
                "Check the indoor power brick: it typically features a dedicated 'Remote Reset' pinhole. "
                "Press and hold the indoor PoE Remote Reset button for 10 seconds to factory reset the outdoor unit safely from ground level."
            ),
            "procedures_by_series": [
                {
                    "series": "Archer Series (AX / C Series)",
                    "reset_time": "8 - 10 seconds",
                    "led_behavior": "All LEDs flash simultaneously or turn solid, then reboot.",
                    "default_ip": "192.168.0.1 or http://tplinkwifi.net",
                    "initial_login": "Prompts to create a new administrator password on first visit."
                },
                {
                    "series": "TL-WR / TL-WDR Series",
                    "reset_time": "6 - 8 seconds",
                    "led_behavior": "SYS LED flashes rapidly.",
                    "default_ip": "192.168.0.1 or 192.168.1.1",
                    "initial_login": "admin / admin"
                },
                {
                    "series": "Deco Mesh System",
                    "reset_time": "1 second",
                    "led_behavior": "LED pulses yellow then blue.",
                    "default_ip": "Configured via Deco Mobile App",
                    "initial_login": "TP-Link Cloud ID"
                },
                {
                    "series": "Outdoor PharOS CPE (CPE210 / CPE510)",
                    "reset_time": "8 - 10 seconds (Remote Reset on PoE Adapter)",
                    "led_behavior": "LAN / RSSI LEDs flash.",
                    "default_ip": "192.168.0.254",
                    "initial_login": "admin / admin"
                }
            ]
        }
