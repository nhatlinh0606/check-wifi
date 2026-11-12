"""
Module: Autonomous Diagnosis Service
Orchestrates the 8-stage autonomous router discovery and recovery diagnosis pipeline.
Streams real-time step progress over WebSocket and synthesizes evidence into a Recovery Plan.
"""

import asyncio
import concurrent.futures
import json
import logging
import os
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

from modules.network_discovery import NetworkDiscovery
from modules.arp_scanner import ArpScanner
from modules.router_identifier import RouterIdentifier
from modules.port_scanner import PortScanner
from modules.admin_interface import AdminInterfaceInspector

from backend.services.websocket_service import ws_manager
from backend.services.wifi_service import WifiService
from backend.services.credential_service import CredentialRecoveryService
from backend.services.decision_engine import RecoveryDecisionEngine, RecoveryPlan

logger = logging.getLogger(__name__)

DIAGNOSIS_STAGES = [
    {"id": 1, "name": "Detecting network interfaces & hardware controllers"},
    {"id": 2, "name": "Scanning wireless environment & radio signals"},
    {"id": 3, "name": "Analyzing Linux routing table, DNS & gateway"},
    {"id": 4, "name": "Discovering gateway devices & local hosts"},
    {"id": 5, "name": "Identifying router vendor & confidence rating"},
    {"id": 6, "name": "Checking router management web interfaces"},
    {"id": 7, "name": "Auditing local credential stores & backup files"},
    {"id": 8, "name": "Generating evidence-based recovery plan"}
]


class DiagnosisService:
    def __init__(self, reports_dir: Optional[str] = None):
        self.status: str = "idle"  # idle, running, completed, failed, cancelled
        self.current_stage: int = 0
        self.stage_message: str = "Ready to start diagnosis"
        self.stages_progress: List[Dict[str, Any]] = [
            {"id": s["id"], "name": s["name"], "status": "pending", "details": None}
            for s in DIAGNOSIS_STAGES
        ]
        self.latest_result: Optional[Dict[str, Any]] = None
        self.error_message: Optional[str] = None
        self._current_task: Optional[asyncio.Task] = None
        self._cancel_requested: bool = False
        self._thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=5)
        self.reports_dir = reports_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "reports"
        )
        os.makedirs(self.reports_dir, exist_ok=True)

    def get_status(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "current_stage": self.current_stage,
            "stage_message": self.stage_message,
            "stages": self.stages_progress,
            "has_result": bool(self.latest_result),
            "error_message": self.error_message,
        }

    async def start_diagnosis(
        self,
        target_interface: Optional[str] = None,
        custom_subnet: Optional[str] = None,
        imported_backup_content: Optional[str] = None,
        imported_backup_filename: Optional[str] = None,
    ) -> bool:
        if self.status == "running":
            logger.warning("Diagnosis already running.")
            return False

        self.status = "running"
        self.current_stage = 0
        self.stage_message = "Starting autonomous diagnosis..."
        self.error_message = None
        self._cancel_requested = False
        self.stages_progress = [
            {"id": s["id"], "name": s["name"], "status": "pending", "details": None}
            for s in DIAGNOSIS_STAGES
        ]

        await ws_manager.broadcast("diagnosis_start", self.get_status())
        self._current_task = asyncio.create_task(
            self._run_diagnosis_pipeline(
                target_interface, custom_subnet, imported_backup_content, imported_backup_filename
            )
        )
        return True

    async def cancel_diagnosis(self) -> bool:
        if self.status != "running":
            return False
        self._cancel_requested = True
        self.status = "cancelled"
        self.stage_message = "Diagnosis cancelled by user."
        if self._current_task and not self._current_task.done():
            self._current_task.cancel()
        await ws_manager.broadcast("diagnosis_cancelled", self.get_status())
        return True

    async def _update_stage(self, stage_num: int, status: str, message: str, details: Any = None):
        self.current_stage = stage_num
        self.stage_message = message
        idx = stage_num - 1
        if 0 <= idx < len(self.stages_progress):
            self.stages_progress[idx]["status"] = status
            if details:
                self.stages_progress[idx]["details"] = details

        await ws_manager.broadcast("diagnosis_progress", {
            "current_stage": self.current_stage,
            "stage_message": self.stage_message,
            "stages": self.stages_progress,
            "status": self.status,
            "stage_update": {
                "id": stage_num,
                "status": status,
                "details": details
            }
        })

    async def _run_diagnosis_pipeline(
        self,
        target_interface: Optional[str],
        custom_subnet: Optional[str],
        backup_content: Optional[str],
        backup_filename: Optional[str],
    ):
        loop = asyncio.get_running_loop()
        try:
            # =========================================================================
            # STAGE 1: Detect Network Interfaces & Hardware Controllers
            # =========================================================================
            await self._update_stage(1, "active", "Detecting system network interfaces and drivers...")

            net_disc = NetworkDiscovery(interface=target_interface)
            all_ifaces = await loop.run_in_executor(self._thread_pool, net_disc.list_interfaces)
            primary_iface = await loop.run_in_executor(self._thread_pool, net_disc.get_active_interface)

            # Discover wireless hardware chipset info via sysfs
            hw_info = await loop.run_in_executor(self._thread_pool, self._get_hardware_controllers)

            stage_1_data = {
                "interfaces": [i.to_dict() for i in all_ifaces],
                "primary_interface": primary_iface.to_dict() if primary_iface else None,
                "hardware_controllers": hw_info
            }
            await self._update_stage(1, "completed", f"Detected {len(all_ifaces)} interface(s)", stage_1_data)

            if self._cancel_requested:
                return

            # =========================================================================
            # STAGE 2: Scanning Wireless Environment
            # =========================================================================
            await self._update_stage(2, "active", "Scanning wireless airwaves for nearby access points...")

            wifi_svc = WifiService()
            wifi_networks = await loop.run_in_executor(
                self._thread_pool,
                lambda: wifi_svc.scan_networks(rescan=False)
            )

            stage_2_data = {
                "networks_count": len(wifi_networks),
                "networks": [n.to_dict() for n in wifi_networks],
                "tplink_aps_detected": [n.to_dict() for n in wifi_networks if n.is_tplink]
            }
            await self._update_stage(
                2, "completed",
                f"Discovered {len(wifi_networks)} Wi-Fi network(s) ({len(stage_2_data['tplink_aps_detected'])} TP-Link)",
                stage_2_data
            )

            if self._cancel_requested:
                return

            # =========================================================================
            # STAGE 3: Analyzing Routing Table, DNS & Gateway
            # =========================================================================
            await self._update_stage(3, "active", "Inspecting routing table, DNS resolvers and DHCP lease...")

            gw_route = await loop.run_in_executor(self._thread_pool, net_disc.get_default_gateway)
            dns_servers = await loop.run_in_executor(self._thread_pool, self._get_dns_servers)

            gateway_ip = gw_route["gateway"] if gw_route else None
            gateway_dev = gw_route["dev"] if gw_route else (primary_iface.name if primary_iface else None)
            target_subnet = custom_subnet or (primary_iface.network if primary_iface else "192.168.1.0/24")

            # Determine connection medium (wifi vs ethernet)
            connection_type = "none"
            if gateway_dev:
                if any(x in gateway_dev for x in ("wl", "wlan", "wifi")):
                    connection_type = "wifi"
                elif any(x in gateway_dev for x in ("eth", "en", "lan")):
                    connection_type = "ethernet"
                else:
                    connection_type = "wifi" if primary_iface and "wl" in primary_iface.name else "ethernet"

            stage_3_data = {
                "default_gateway": gateway_ip,
                "gateway_interface": gateway_dev,
                "connection_type": connection_type,
                "target_subnet": target_subnet,
                "dns_servers": dns_servers
            }
            await self._update_stage(
                3, "completed",
                f"Default Gateway: {gateway_ip or 'None'} via {gateway_dev or 'Unknown'} ({connection_type})",
                stage_3_data
            )

            if self._cancel_requested:
                return

            # =========================================================================
            # STAGE 4: Discovering Gateway Devices & Local Hosts
            # =========================================================================
            await self._update_stage(4, "active", f"Sweeping subnet {target_subnet} for live hosts and ARP entries...")

            arp_scanner = ArpScanner(interface=gateway_dev)
            discovered_hosts = await loop.run_in_executor(
                self._thread_pool,
                lambda: arp_scanner.scan_subnet(subnet_cidr=target_subnet)
            )

            stage_4_data = {
                "hosts_count": len(discovered_hosts),
                "hosts": [h.to_dict() for h in discovered_hosts]
            }
            await self._update_stage(
                4, "completed",
                f"Discovered {len(discovered_hosts)} active host(s) on local subnet",
                stage_4_data
            )

            if self._cancel_requested:
                return

            # =========================================================================
            # STAGE 5: Identifying Router Vendor & Confidence Rating
            # =========================================================================
            await self._update_stage(5, "active", "Analyzing MAC OUIs, device roles and vendor signatures...")

            router_id = RouterIdentifier()
            identified_devices = []
            gateway_candidate = None

            for h in discovered_hosts:
                if self._cancel_requested:
                    return

                res = await loop.run_in_executor(
                    self._thread_pool,
                    lambda host=h: router_id.identify_device(
                        ip=host.ip,
                        mac=host.mac,
                        is_gateway=host.is_gateway,
                        scan_ports=False,  # ports scanned in stage 6
                        inspect_web=False
                    )
                )
                res_dict = res.to_dict()
                identified_devices.append(res_dict)
                if res.is_gateway or res.ip == gateway_ip:
                    gateway_candidate = res_dict

            detected_vendor = gateway_candidate.get("detected_vendor", "Unknown") if gateway_candidate else "Unknown"
            is_tplink = gateway_candidate.get("is_tplink_candidate", False) if gateway_candidate else False

            stage_5_data = {
                "gateway_device": gateway_candidate,
                "detected_vendor": detected_vendor,
                "is_tplink_candidate": is_tplink,
                "candidate_devices": identified_devices
            }
            await self._update_stage(
                5, "completed",
                f"Gateway Vendor: {detected_vendor} (TP-Link candidate: {is_tplink})",
                stage_5_data
            )

            if self._cancel_requested:
                return

            # =========================================================================
            # STAGE 6: Checking Router Management Web Interfaces
            # =========================================================================
            await self._update_stage(6, "active", f"Inspecting management web ports on gateway {gateway_ip}...")

            port_scanner = PortScanner()
            admin_inspector = AdminInterfaceInspector()
            mgmt_endpoints: List[Dict[str, Any]] = []
            open_ports: List[int] = []
            model_hint: Optional[str] = None

            if gateway_ip:
                port_results = await loop.run_in_executor(
                    self._thread_pool,
                    lambda: port_scanner.scan_host(gateway_ip)
                )
                open_ports = [p.port for p in port_results if p.is_open]

                web_ports = [p for p in open_ports if p in (80, 443, 8080, 8443)]
                if web_ports:
                    endpoints = await loop.run_in_executor(
                        self._thread_pool,
                        lambda: admin_inspector.inspect_host(gateway_ip, ports=web_ports)
                    )
                    mgmt_endpoints = [ep.to_dict() for ep in endpoints]
                    for ep in endpoints:
                        if ep.model_hint:
                            model_hint = ep.model_hint
                            break

            stage_6_data = {
                "gateway_ip": gateway_ip,
                "open_ports": open_ports,
                "management_endpoints": mgmt_endpoints,
                "is_management_reachable": bool(mgmt_endpoints),
                "model_hint": model_hint
            }
            await self._update_stage(
                6, "completed",
                f"Management Web UI: {'Reachable' if mgmt_endpoints else 'Not reachable'} (Ports: {', '.join(map(str, open_ports)) or 'None'})",
                stage_6_data
            )

            if self._cancel_requested:
                return

            # =========================================================================
            # STAGE 7: Auditing Local Credential Stores & Backup Files
            # =========================================================================
            await self._update_stage(7, "active", "Querying legitimate local credential sources...")

            cred_sources = await loop.run_in_executor(
                self._thread_pool,
                lambda: CredentialRecoveryService.audit_all_sources(
                    target_ssid=primary_iface.name if primary_iface else None,
                    imported_backup_content=backup_content,
                    imported_backup_filename=backup_filename
                )
            )

            stage_7_data = {
                "sources_checked_count": len(cred_sources),
                "sources": [cs.to_dict() for cs in cred_sources],
                "matching_credential_found": any(cs.matching_credential_found for cs in cred_sources)
            }
            await self._update_stage(
                7, "completed",
                f"Audited {len(cred_sources)} source(s): {'Credentials found' if stage_7_data['matching_credential_found'] else 'No stored credentials'}",
                stage_7_data
            )

            if self._cancel_requested:
                return

            # =========================================================================
            # STAGE 8: Generating Evidence-Based Recovery Plan
            # =========================================================================
            await self._update_stage(8, "active", "Synthesizing evidence into an actionable recovery plan...")

            nearby_ssid_names = [n.ssid for n in wifi_networks]

            plan: RecoveryPlan = await loop.run_in_executor(
                self._thread_pool,
                lambda: RecoveryDecisionEngine.evaluate(
                    has_network_connection=bool(gateway_ip),
                    connection_type=connection_type,
                    gateway_ip=gateway_ip,
                    gateway_mac=gateway_candidate.get("mac") if gateway_candidate else None,
                    detected_vendor=detected_vendor,
                    is_tplink_candidate=is_tplink,
                    model_hint=model_hint,
                    management_endpoints=mgmt_endpoints,
                    credential_sources=[cs.to_dict() for cs in cred_sources],
                    nearby_ssids=nearby_ssid_names,
                    active_interface_name=primary_iface.name if primary_iface else None,
                )
            )

            stage_8_data = plan.to_dict()
            await self._update_stage(
                8, "completed",
                f"Recovery Plan Ready: {plan.scenario_title}",
                stage_8_data
            )

            # Compile Full Diagnosis Report
            timestamp = datetime.now().isoformat()
            full_diagnosis = {
                "timestamp": timestamp,
                "environment": stage_1_data,
                "wireless": stage_2_data,
                "routing": stage_3_data,
                "hosts": stage_4_data,
                "router_identification": stage_5_data,
                "management": stage_6_data,
                "credentials": stage_7_data,
                "recovery_plan": stage_8_data,
            }

            self.latest_result = full_diagnosis
            self.status = "completed"
            self.stage_message = f"Diagnosis complete. Scenario: {plan.scenario_title}"

            # Save report to reports/
            report_filename = f"diagnosis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            report_path = os.path.join(self.reports_dir, report_filename)
            try:
                with open(report_path, "w", encoding="utf-8") as f:
                    json.dump(full_diagnosis, f, indent=2)
            except Exception as e:
                logger.warning(f"Could not save diagnosis JSON: {e}")

            await ws_manager.broadcast("diagnosis_complete", {
                "status": self.status,
                "stage_message": self.stage_message,
                "result": full_diagnosis
            })

        except asyncio.CancelledError:
            self.status = "cancelled"
            self.stage_message = "Diagnosis was cancelled."
            await ws_manager.broadcast("diagnosis_cancelled", self.get_status())
        except Exception as e:
            logger.error(f"Diagnosis pipeline failed: {e}", exc_info=True)
            self.status = "failed"
            self.error_message = str(e)
            self.stage_message = f"Error during diagnosis: {e}"
            await ws_manager.broadcast("diagnosis_error", self.get_status())

    @staticmethod
    def _get_hardware_controllers() -> List[Dict[str, str]]:
        """Reads network controllers driver / chipset via sysfs and lspci."""
        controllers = []
        sysfs_net = "/sys/class/net"
        if os.path.exists(sysfs_net):
            for iface in os.listdir(sysfs_net):
                if iface == "lo":
                    continue
                dev_path = os.path.join(sysfs_net, iface, "device")
                driver = None
                pci_id = None
                if os.path.exists(dev_path):
                    uevent_file = os.path.join(dev_path, "uevent")
                    if os.path.exists(uevent_file):
                        try:
                            with open(uevent_file, "r") as f:
                                for line in f:
                                    if line.startswith("DRIVER="):
                                        driver = line.strip().split("=")[1]
                                    elif line.startswith("PCI_ID="):
                                        pci_id = line.strip().split("=")[1]
                        except Exception:
                            pass
                controllers.append({
                    "interface": iface,
                    "driver": driver or "Standard Linux net_device",
                    "chipset_pci_id": pci_id or "Integrated / USB"
                })
        return controllers

    @staticmethod
    def _get_dns_servers() -> List[str]:
        """Parses active DNS servers from systemd-resolve or resolv.conf."""
        dns = []
        try:
            res = subprocess.run(["resolvectl", "status"], capture_output=True, text=True, timeout=2, check=False)
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    if "DNS Servers:" in line or "Current DNS Server:" in line:
                        parts = line.split(":")
                        if len(parts) > 1:
                            for ip in parts[1].split():
                                if ip.strip() and ip.strip() not in dns:
                                    dns.append(ip.strip())
        except Exception:
            pass

        if not dns and os.path.exists("/etc/resolv.conf"):
            try:
                with open("/etc/resolv.conf", "r") as f:
                    for line in f:
                        if line.startswith("nameserver"):
                            parts = line.split()
                            if len(parts) > 1 and parts[1] != "127.0.0.53":
                                dns.append(parts[1])
            except Exception:
                pass
        return dns


diagnosis_manager = DiagnosisService()
