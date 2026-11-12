#!/usr/bin/env python3
"""
Module: Port Discovery
Performs safe, non-intrusive TCP connect checks on common router administration ports.
Default target ports: 80 (HTTP), 443 (HTTPS), 8080 (HTTP-Alt), 8443 (HTTPS-Alt), 22 (SSH), 23 (Telnet).
"""

import concurrent.futures
import logging
import socket
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

COMMON_ROUTER_PORTS = {
    80: "HTTP",
    443: "HTTPS",
    8080: "HTTP-Alt",
    8443: "HTTPS-Alt",
    22: "SSH",
    23: "Telnet"
}


@dataclass
class PortScanResult:
    port: int
    service: str
    is_open: bool
    latency_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PortScanner:
    """Checks TCP connectivity on specific administrative ports."""

    def __init__(self, ports: Optional[Dict[int, str]] = None, timeout: float = 0.8, max_workers: int = 10):
        self.ports = ports or COMMON_ROUTER_PORTS
        self.timeout = timeout
        self.max_workers = max_workers

    def check_port(self, host: str, port: int, service: str) -> PortScanResult:
        """Attempts a standard TCP 3-way handshake to test port availability."""
        start_time = time.perf_counter()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        try:
            res = sock.connect_ex((host, port))
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            if res == 0:
                return PortScanResult(port=port, service=service, is_open=True, latency_ms=elapsed_ms)
        except Exception as e:
            logger.debug(f"Port check error {host}:{port}: {e}")
        finally:
            try:
                sock.close()
            except Exception:
                pass
        return PortScanResult(port=port, service=service, is_open=False)

    def scan_host(self, host: str) -> List[PortScanResult]:
        """Scans all configured ports on a single host in parallel."""
        results: List[PortScanResult] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(self.max_workers, len(self.ports))) as executor:
            future_to_port = {
                executor.submit(self.check_port, host, port, srv): port
                for port, srv in self.ports.items()
            }
            for future in concurrent.futures.as_completed(future_to_port):
                res = future.result()
                if res.is_open:
                    results.append(res)

        return sorted(results, key=lambda x: x.port)

    def get_open_web_ports(self, scan_results: List[PortScanResult]) -> List[int]:
        """Extracts open web ports (HTTP / HTTPS) from scan results."""
        web_ports = []
        for r in scan_results:
            if r.is_open and r.port in (80, 443, 8080, 8443):
                web_ports.append(r.port)
        return web_ports
