#!/usr/bin/env python3
"""
Module: ARP & Host Discovery
Discovers live hosts in the target subnet using ARP requests (Scapy when privileged)
and multi-threaded ping / TCP sweep fallback for non-root users.
"""

import concurrent.futures
import ipaddress
import logging
import os
import socket
import subprocess
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any

from .network_discovery import NetworkDiscovery

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredHost:
    ip: str
    mac: str
    hostname: Optional[str] = None
    interface: Optional[str] = None
    is_gateway: bool = False
    vendor: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ArpScanner:
    """Discovers hosts on the local network using ARP or ping sweep."""

    def __init__(self, interface: Optional[str] = None, timeout: float = 1.5, max_workers: int = 50):
        self.interface = interface
        self.timeout = timeout
        self.max_workers = max_workers
        self.net_discovery = NetworkDiscovery(interface=interface)

    def scan_subnet(self, subnet_cidr: Optional[str] = None) -> List[DiscoveredHost]:
        """
        Scans subnet to discover live hosts.
        If subnet_cidr is not specified, uses active interface's network.
        """
        iface_info = self.net_discovery.get_active_interface()
        if not iface_info and not subnet_cidr:
            logger.error("No active network interface found and no subnet specified.")
            return []

        target_subnet = subnet_cidr or iface_info.network
        gateway_ip = iface_info.gateway if iface_info else None
        target_iface = self.interface or (iface_info.name if iface_info else None)

        logger.info(f"Scanning subnet {target_subnet} on interface {target_iface}...")

        hosts_dict: Dict[str, DiscoveredHost] = {}

        # 1. Read existing ARP cache
        initial_arp = self.net_discovery.get_arp_table(interface=target_iface)
        for entry in initial_arp:
            ip = entry["ip"]
            # Exclude IPv6 or broadcast
            if ":" not in ip and ip != "255.255.255.255":
                hosts_dict[ip] = DiscoveredHost(
                    ip=ip,
                    mac=entry["mac"],
                    interface=entry["dev"],
                    is_gateway=(ip == gateway_ip)
                )

        # 2. Try Scapy ARP scan if running as root
        scapy_success = False
        if os.geteuid() == 0:
            try:
                from scapy.all import srp, Ether, ARP, conf
                conf.verb = 0
                logger.info(f"Running Scapy ARP scan on {target_subnet}...")
                ans, _ = srp(
                    Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=target_subnet),
                    timeout=self.timeout,
                    iface=target_iface,
                    verbose=False
                )
                for snd, rcv in ans:
                    ip = rcv.psrc
                    mac = rcv.hwsrc.lower()
                    hosts_dict[ip] = DiscoveredHost(
                        ip=ip,
                        mac=mac,
                        interface=target_iface,
                        is_gateway=(ip == gateway_ip)
                    )
                scapy_success = True
            except Exception as e:
                logger.debug(f"Scapy ARP scan failed or not permitted: {e}")

        # 3. If Scapy was not run or returned few results, run parallel ping sweep to trigger ARP
        if not scapy_success:
            logger.info("Performing fast parallel ping/TCP probe sweep to refresh ARP cache...")
            self._probe_subnet(target_subnet)
            # Re-read ARP cache
            refreshed_arp = self.net_discovery.get_arp_table(interface=target_iface)
            for entry in refreshed_arp:
                ip = entry["ip"]
                if ":" not in ip and ip != "255.255.255.255":
                    hosts_dict[ip] = DiscoveredHost(
                        ip=ip,
                        mac=entry["mac"],
                        interface=entry["dev"],
                        is_gateway=(ip == gateway_ip)
                    )

        # 4. Resolve hostnames in parallel
        host_list = list(hosts_dict.values())
        self._enrich_hostnames(host_list)

        # Ensure gateway is flagged
        for h in host_list:
            if h.ip == gateway_ip:
                h.is_gateway = True

        return sorted(host_list, key=lambda x: [int(p) for p in x.ip.split(".") if p.isdigit()])

    def _probe_subnet(self, subnet_cidr: str) -> None:
        """Pings all hosts in the subnet (limits to /24 size to prevent flooding)."""
        try:
            network = ipaddress.ip_network(subnet_cidr, strict=False)
            # Limit scan to at most 256 hosts for speed and safety
            hosts = list(network.hosts())[:256]
        except Exception as e:
            logger.error(f"Invalid subnet {subnet_cidr}: {e}")
            return

        def probe_host(ip_str: str):
            # Fast ping probe: 1 packet, 0.4s timeout
            try:
                subprocess.run(
                    ["ping", "-c", "1", "-W", "1", ip_str],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=1.0
                )
            except Exception:
                pass

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            executor.map(probe_host, [str(h) for h in hosts])

    def _enrich_hostnames(self, hosts: List[DiscoveredHost]) -> None:
        """Resolves hostnames concurrently."""
        def resolve(host: DiscoveredHost):
            name = NetworkDiscovery.resolve_hostname(host.ip, timeout=0.4)
            if name:
                host.hostname = name

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            executor.map(resolve, hosts)
