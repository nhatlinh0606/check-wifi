"""
Scan Service
Coordinates asynchronous background network discovery and streams live progress
to frontend clients through the WebSocket service.
"""

import asyncio
import concurrent.futures
import logging
from typing import Dict, List, Optional, Any

from modules.network_discovery import NetworkDiscovery
from modules.arp_scanner import ArpScanner
from modules.router_identifier import RouterIdentifier
from modules.reporter import DiscoveryReporter
from backend.services.websocket_service import ws_manager

logger = logging.getLogger(__name__)


class ScanService:
    def __init__(self):
        self.status: str = "idle"  # idle, running, completed, failed, cancelled
        self.progress: int = 0
        self.current_step: str = "Ready"
        self.interface_info: Optional[Dict[str, Any]] = None
        self.discovered_devices: List[Dict[str, Any]] = []
        self.last_report_file: Optional[str] = None
        self.error_message: Optional[str] = None
        self._current_task: Optional[asyncio.Task] = None
        self._cancel_requested: bool = False
        self._thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

    def get_status(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "progress": self.progress,
            "current_step": self.current_step,
            "interface_info": self.interface_info,
            "discovered_devices": self.discovered_devices,
            "devices_count": len(self.discovered_devices),
            "tplink_count": sum(1 for d in self.discovered_devices if d.get("is_tplink_candidate")),
            "last_report_file": self.last_report_file,
            "error_message": self.error_message,
        }

    async def start_scan(self, interface: Optional[str] = None, subnet: Optional[str] = None) -> bool:
        if self.status == "running":
            logger.warning("Scan already running.")
            return False

        self.status = "running"
        self.progress = 5
        self.current_step = "Initializing discovery..."
        self.discovered_devices = []
        self.last_report_file = None
        self.error_message = None
        self._cancel_requested = False

        await ws_manager.broadcast("scan_start", self.get_status())
        self._current_task = asyncio.create_task(self._run_scan_async(interface, subnet))
        return True

    async def cancel_scan(self) -> bool:
        if self.status != "running":
            return False

        self._cancel_requested = True
        self.status = "cancelled"
        self.current_step = "Scan cancelled by user."
        if self._current_task and not self._current_task.done():
            self._current_task.cancel()

        await ws_manager.broadcast("scan_progress", self.get_status())
        return True

    async def _run_scan_async(self, interface: Optional[str], subnet: Optional[str]):
        loop = asyncio.get_running_loop()
        try:
            # Step 1: Detect Network Interface
            self.progress = 10
            self.current_step = "Detecting active network interface and routing..."
            await ws_manager.broadcast("scan_progress", self.get_status())

            net_disc = NetworkDiscovery(interface=interface)
            iface_info = await loop.run_in_executor(self._thread_pool, net_disc.get_active_interface)

            if not iface_info:
                raise ValueError("No active network interface with IPv4 detected.")

            self.interface_info = iface_info.to_dict()
            target_subnet = subnet or iface_info.network

            # Step 2: Subnet ARP / Ping Sweep
            if self._cancel_requested:
                return

            self.progress = 25
            self.current_step = f"Scanning subnet {target_subnet} for live hosts..."
            await ws_manager.broadcast("scan_progress", self.get_status())

            arp_scanner = ArpScanner(interface=iface_info.name)
            hosts = await loop.run_in_executor(
                self._thread_pool,
                lambda: arp_scanner.scan_subnet(subnet_cidr=target_subnet)
            )

            if self._cancel_requested:
                return

            self.progress = 45
            self.current_step = f"Discovered {len(hosts)} active host(s). Beginning router identification..."
            await ws_manager.broadcast("scan_progress", self.get_status())

            # Step 3: Inspect each host incrementally and broadcast
            router_id = RouterIdentifier()
            results = []
            total_hosts = max(1, len(hosts))

            for idx, host in enumerate(hosts):
                if self._cancel_requested:
                    return

                res = await loop.run_in_executor(
                    self._thread_pool,
                    lambda h=host: router_id.identify_device(
                        ip=h.ip,
                        mac=h.mac,
                        is_gateway=h.is_gateway,
                        scan_ports=True,
                        inspect_web=True
                    )
                )

                res_dict = res.to_dict()
                self.discovered_devices.append(res_dict)
                results.append(res)

                # Incremental progress (45% to 90%)
                step_progress = 45 + int(((idx + 1) / total_hosts) * 45)
                self.progress = min(90, step_progress)
                self.current_step = f"Analyzed {host.ip} ({res.detected_vendor}) [{idx + 1}/{total_hosts}]"

                # Broadcast incremental device finding
                await ws_manager.broadcast("device_found", {
                    "device": res_dict,
                    "progress": self.progress,
                    "current_step": self.current_step
                })

            # Step 4: Export report
            if self._cancel_requested:
                return

            self.progress = 95
            self.current_step = "Generating diagnostic report..."
            await ws_manager.broadcast("scan_progress", self.get_status())

            reporter = DiscoveryReporter()
            out_file = await loop.run_in_executor(
                self._thread_pool,
                lambda: reporter.export_json(iface_info, results)
            )
            self.last_report_file = out_file

            self.progress = 100
            self.status = "completed"
            self.current_step = f"Discovery complete. Found {len(self.discovered_devices)} device(s)."
            await ws_manager.broadcast("scan_complete", self.get_status())

        except asyncio.CancelledError:
            self.status = "cancelled"
            self.current_step = "Scan was cancelled."
            await ws_manager.broadcast("scan_progress", self.get_status())
        except Exception as e:
            logger.error(f"Scan failed: {e}", exc_info=True)
            self.status = "failed"
            self.error_message = str(e)
            self.current_step = f"Error: {e}"
            await ws_manager.broadcast("scan_error", self.get_status())


scan_manager = ScanService()
