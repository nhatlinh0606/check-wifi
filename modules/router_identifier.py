#!/usr/bin/env python3
"""
Module: Router Identification
Identifies devices on the network, determines whether they are TP-Link routers,
and computes a Confidence Level (High, Medium, Low, None) based on:
1. MAC OUI Vendor database (config/vendors.json + IEEE oui.txt fallback)
2. Default gateway role
3. Open administration ports (80, 443, etc.)
4. HTTP/HTTPS responses, headers, page titles, and firmware signatures
"""

import json
import logging
import os
import re
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any

from .admin_interface import AdminEndpointInfo, AdminInterfaceInspector
from .port_scanner import PortScanResult, PortScanner

logger = logging.getLogger(__name__)


@dataclass
class RouterIdentificationResult:
    ip: str
    mac: Optional[str]
    is_gateway: bool
    detected_vendor: str
    is_tplink_candidate: bool
    confidence: str  # High, Medium, Low, None
    confidence_score: int  # 0 to 100
    evidence: List[str] = field(default_factory=list)
    model_hint: Optional[str] = None
    admin_url: Optional[str] = None
    open_ports: List[int] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RouterIdentifier:
    """Evaluates candidate devices to identify router brand and management interfaces."""

    def __init__(self, vendors_config_path: Optional[str] = None):
        self.vendors_db: Dict[str, List[str]] = {}
        self.config_path = vendors_config_path or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "config", "vendors.json"
        )
        self._load_vendors()
        self.port_scanner = PortScanner()
        self.admin_inspector = AdminInterfaceInspector()

    def _load_vendors(self) -> None:
        """Loads MAC OUI database from config/vendors.json."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.vendors_db = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load vendors JSON: {e}")
        else:
            logger.warning(f"Vendors config not found at {self.config_path}")

    def lookup_mac_vendor(self, mac: Optional[str]) -> str:
        """Determines vendor by MAC OUI prefix (XX:XX:XX)."""
        if not mac or len(mac) < 8:
            return "Unknown"

        normalized_mac = mac.upper().replace("-", ":")
        prefix = ":".join(normalized_mac.split(":")[:3])

        # Check in our vendors database
        for vendor, ouis in self.vendors_db.items():
            if prefix in ouis:
                return vendor

        # Check system IEEE oui.txt if present
        sys_oui = "/var/lib/ieee-data/oui.txt"
        if os.path.exists(sys_oui):
            try:
                search_prefix = prefix.replace(":", "-")
                with open(sys_oui, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if line.startswith(search_prefix) and "(hex)" in line:
                            parts = line.split("(hex)")
                            if len(parts) > 1:
                                return parts[1].strip()
            except Exception:
                pass

        return "Unknown"

    def identify_device(
        self,
        ip: str,
        mac: Optional[str] = None,
        is_gateway: bool = False,
        scan_ports: bool = True,
        inspect_web: bool = True
    ) -> RouterIdentificationResult:
        """
        Runs comprehensive identification on a single IP address.
        """
        score = 0
        evidence: List[str] = []
        detected_vendor = self.lookup_mac_vendor(mac)
        is_tplink_oui = "TP-LINK" in detected_vendor.upper()

        if mac:
            if is_tplink_oui:
                score += 40
                evidence.append(f"MAC OUI prefix ({mac[:8]}) matches TP-Link registered vendor.")
            elif detected_vendor != "Unknown":
                evidence.append(f"MAC OUI prefix matches {detected_vendor}.")
                # If definitely another vendor, penalize TP-Link score
                score -= 30
            else:
                evidence.append(f"MAC address {mac} has unlisted OUI vendor.")

        if is_gateway:
            score += 25
            evidence.append("Device operates as the default gateway for this network.")

        open_ports: List[int] = []
        port_results: List[PortScanResult] = []
        if scan_ports:
            port_results = self.port_scanner.scan_host(ip)
            open_ports = [p.port for p in port_results]
            if open_ports:
                evidence.append(f"Open administrative ports detected: {', '.join(map(str, open_ports))}.")
                if 80 in open_ports or 443 in open_ports or 8080 in open_ports:
                    score += 15

        admin_endpoints: List[AdminEndpointInfo] = []
        model_hint: Optional[str] = None
        best_admin_url: Optional[str] = None
        has_tplink_web_sig = False

        # Check for non-TP-Link signatures in title or headers
        other_vendor_patterns = [
            (r"(F660\w*|F670\w*|ZXHN\w*|ZTE\b)", "ZTE"),
            (r"(HG8\w*|EchoLife\w*|OptiXstar\w*|Huawei\b)", "Huawei"),
            (r"(ASUSWRT|RT-AC\w*|RT-AX\w*|ZenWiFi|Asus\b)", "ASUS"),
            (r"(NETGEAR\b|Nighthawk\b|Orbi\b)", "NETGEAR"),
            (r"(D-Link\b|DIR-\w+)", "D-LINK"),
            (r"(Mi Router\b|MiWiFi|Redmi\s+Router)", "XIAOMI"),
            (r"(Tenda\b)", "TENDA"),
            (r"(TOTOLINK\b)", "TOTOLINK"),
        ]

        if inspect_web and open_ports:
            web_ports = [p for p in open_ports if p in (80, 443, 8080, 8443)]
            if web_ports:
                admin_endpoints = self.admin_inspector.inspect_host(ip, web_ports)
                for ep in admin_endpoints:
                    if not best_admin_url:
                        best_admin_url = ep.final_url or ep.url

                    if ep.title:
                        evidence.append(f"Web interface title: '{ep.title}' at {ep.url}")
                        for pat, vname in other_vendor_patterns:
                            if re.search(pat, ep.title, re.IGNORECASE):
                                evidence.append(f"Web title matches signature of {vname} ({ep.title}).")
                                if detected_vendor in ("Unknown", "ZTE", "Huawei", "ASUS"):
                                    detected_vendor = vname
                                score -= 40
                                break

                    if ep.server_header:
                        for pat, vname in other_vendor_patterns:
                            if re.search(pat, ep.server_header, re.IGNORECASE):
                                evidence.append(f"Server header matches {vname}: {ep.server_header}")
                                detected_vendor = vname
                                score -= 40
                                break

                    if ep.tplink_signatures_found:
                        has_tplink_web_sig = True
                        score += 50
                        detected_vendor = "TP-Link"
                        evidence.append(f"TP-Link signatures found in HTTP response: {', '.join(ep.tplink_signatures_found)}")

                    if ep.model_hint:
                        model_hint = ep.model_hint
                        evidence.append(f"TP-Link Model signature detected: {model_hint}")
                        score += 25

        # Adjust score bounds
        final_score = max(0, min(100, score))

        # Determine confidence level
        if final_score >= 65:
            confidence = "High"
            is_tplink_candidate = True
        elif final_score >= 40:
            confidence = "Medium"
            is_tplink_candidate = True
        elif final_score >= 20:
            confidence = "Low"
            is_tplink_candidate = (is_tplink_oui or has_tplink_web_sig)
        else:
            confidence = "None"
            is_tplink_candidate = False

        if not is_tplink_oui and detected_vendor != "Unknown":
            # Display the real detected vendor
            pass
        elif is_tplink_oui:
            detected_vendor = "TP-Link"

        return RouterIdentificationResult(
            ip=ip,
            mac=mac,
            is_gateway=is_gateway,
            detected_vendor=detected_vendor,
            is_tplink_candidate=is_tplink_candidate,
            confidence=confidence,
            confidence_score=final_score,
            evidence=evidence,
            model_hint=model_hint,
            admin_url=best_admin_url,
            open_ports=open_ports,
            details={
                "endpoints": [ep.to_dict() for ep in admin_endpoints],
                "port_results": [p.to_dict() for p in port_results]
            }
        )
