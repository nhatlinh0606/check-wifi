#!/usr/bin/env python3
"""
Module: Network Discovery
Provides network interface detection, routing table inspection,
subnet calculation, and ARP cache inspection for Ubuntu Linux.
"""

import json
import logging
import os
import re
import socket
import subprocess
from dataclasses import dataclass, asdict
from ipaddress import IPv4Network, IPv4Interface
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


@dataclass
class NetworkInterfaceInfo:
    name: str
    ip: str
    netmask: str
    cidr: str
    network: str
    mac: str
    is_up: bool
    is_default: bool
    gateway: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class NetworkDiscovery:
    """Discovers local network interfaces, routes, gateways, and ARP neighbors."""

    def __init__(self, interface: Optional[str] = None):
        self.interface_override = interface

    def get_default_gateway(self) -> Optional[Dict[str, str]]:
        """
        Determines the default gateway IP and interface.
        Tries `ip -j route show default`, falls back to parsing /proc/net/route.
        """
        # Method 1: ip -j route show default
        try:
            res = subprocess.run(
                ["ip", "-j", "route", "show", "default"],
                capture_output=True,
                text=True,
                timeout=3,
                check=False
            )
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout)
                for entry in data:
                    if entry.get("dst") == "default" and "gateway" in entry:
                        return {
                            "gateway": entry["gateway"],
                            "dev": entry.get("dev", "")
                        }
        except Exception as e:
            logger.debug(f"iproute2 default route lookup failed: {e}")

        # Method 2: Fallback /proc/net/route
        try:
            if os.path.exists("/proc/net/route"):
                with open("/proc/net/route", "r") as f:
                    for line in f.readlines()[1:]:
                        parts = line.strip().split()
                        if len(parts) >= 3 and parts[1] == "00000000":
                            dev = parts[0]
                            gw_hex = parts[2]
                            # Little endian hex to IP
                            gw_bytes = bytes.fromhex(gw_hex)
                            gw_ip = socket.inet_ntoa(gw_bytes[::-1])
                            return {"gateway": gw_ip, "dev": dev}
        except Exception as e:
            logger.debug(f"/proc/net/route lookup failed: {e}")

        # Method 3: Socket trick to find route to public IP
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                # Just checks outbound interface, gateway usually 192.168.x.1
                # But we don't have gateway IP directly here.
        except Exception:
            pass

        return None

    def list_interfaces(self) -> List[NetworkInterfaceInfo]:
        """Lists all network interfaces with active IPv4 addresses."""
        interfaces: List[NetworkInterfaceInfo] = []
        default_route = self.get_default_gateway()
        default_dev = default_route["dev"] if default_route else None
        default_gw = default_route["gateway"] if default_route else None

        # Method 1: ip -j addr show
        try:
            res = subprocess.run(
                ["ip", "-j", "addr", "show"],
                capture_output=True,
                text=True,
                timeout=3,
                check=False
            )
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout)
                for item in data:
                    ifname = item.get("ifname", "")
                    if ifname == "lo":
                        continue
                    flags = item.get("flags", [])
                    is_up = "UP" in flags
                    mac = item.get("address", "")

                    for addr in item.get("addr_info", []):
                        if addr.get("family") == "inet":
                            ip = addr.get("local")
                            prefixlen = addr.get("prefixlen")
                            if ip and prefixlen:
                                iface_obj = IPv4Interface(f"{ip}/{prefixlen}")
                                is_def = (ifname == default_dev)
                                interfaces.append(
                                    NetworkInterfaceInfo(
                                        name=ifname,
                                        ip=ip,
                                        netmask=str(iface_obj.netmask),
                                        cidr=f"{ip}/{prefixlen}",
                                        network=str(iface_obj.network),
                                        mac=mac,
                                        is_up=is_up,
                                        is_default=is_def,
                                        gateway=default_gw if is_def else None
                                    )
                                )
                if interfaces:
                    return interfaces
        except Exception as e:
            logger.debug(f"ip -j addr show failed: {e}")

        return interfaces

    def get_active_interface(self) -> Optional[NetworkInterfaceInfo]:
        """
        Gets the primary interface.
        If interface_override was given, looks up that interface.
        Otherwise picks the default route interface, or first UP interface.
        """
        all_ifaces = self.list_interfaces()
        if not all_ifaces:
            return None

        if self.interface_override:
            for iface in all_ifaces:
                if iface.name == self.interface_override:
                    return iface
            logger.warning(f"Interface '{self.interface_override}' not found among active interfaces.")

        # Default route interface
        for iface in all_ifaces:
            if iface.is_default:
                return iface

        # First UP interface
        for iface in all_ifaces:
            if iface.is_up:
                return iface

        return all_ifaces[0]

    def get_arp_table(self, interface: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Reads system ARP neighbor table.
        Returns list of dicts: [{'ip': ..., 'mac': ..., 'dev': ..., 'state': ...}]
        """
        results: List[Dict[str, str]] = []

        # Method 1: ip -j neigh show
        try:
            cmd = ["ip", "-j", "neigh", "show"]
            if interface:
                cmd.extend(["dev", interface])
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=3, check=False)
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout)
                for entry in data:
                    ip = entry.get("dst")
                    mac = entry.get("lladdr")
                    dev = entry.get("dev", "")
                    state = ",".join(entry.get("state", []))
                    if ip and mac and "FAILED" not in state:
                        results.append({
                            "ip": ip,
                            "mac": mac.lower(),
                            "dev": dev,
                            "state": state
                        })
                if results:
                    return results
        except Exception as e:
            logger.debug(f"ip -j neigh show failed: {e}")

        # Method 2: /proc/net/arp fallback
        try:
            if os.path.exists("/proc/net/arp"):
                with open("/proc/net/arp", "r") as f:
                    lines = f.readlines()[1:]
                    for line in lines:
                        parts = line.strip().split()
                        if len(parts) >= 6:
                            ip, _, flags, mac, _, dev = parts[:6]
                            if flags != "0x0" and mac != "00:00:00:00:00:00":
                                if interface and dev != interface:
                                    continue
                                results.append({
                                    "ip": ip,
                                    "mac": mac.lower(),
                                    "dev": dev,
                                    "state": "REACHABLE"
                                })
        except Exception as e:
            logger.debug(f"/proc/net/arp parsing failed: {e}")

        return results

    @staticmethod
    def resolve_hostname(ip: str, timeout: float = 0.5) -> Optional[str]:
        """Resolves hostname via reverse DNS with a short socket timeout."""
        default_timeout = socket.getdefaulttimeout()
        try:
            socket.setdefaulttimeout(timeout)
            hostname, _, _ = socket.gethostbyaddr(ip)
            return hostname
        except Exception:
            return None
        finally:
            socket.setdefaulttimeout(default_timeout)
