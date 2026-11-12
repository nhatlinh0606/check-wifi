#!/usr/bin/env python3
"""
Module: Admin Interface Discovery
Inspects HTTP and HTTPS endpoints of discovered devices to collect status codes,
redirects, page titles, and web signatures associated with TP-Link routers.
Performs strictly passive reading: NO login attempts or credential testing.
"""

import html
import logging
import re
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
import requests
import urllib3

# Suppress SSL certificate warnings for router self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

# Known TP-Link signatures in HTML, headers, or URLs
TPLINK_SIGNATURES = [
    r"tp-link",
    r"tplink",
    r"tplinkwifi\.net",
    r"tplinklogin\.net",
    r"tplinkmodem\.net",
    r"tplinkap\.net",
    r"archer\s+[a-z0-9]+",
    r"deco\s+[a-z0-9]+",
    r"tl-wr[0-9]+",
    r"tl-wdr[0-9]+",
    r"tl-mr[0-9]+",
    r"tp-link\s+technologies",
]


@dataclass
class AdminEndpointInfo:
    url: str
    port: int
    protocol: str
    status_code: int
    title: Optional[str] = None
    server_header: Optional[str] = None
    redirect_chain: List[str] = field(default_factory=list)
    final_url: Optional[str] = None
    auth_realm: Optional[str] = None
    tplink_signatures_found: List[str] = field(default_factory=list)
    model_hint: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AdminInterfaceInspector:
    """Passively queries web management endpoints on candidate devices."""

    def __init__(self, timeout: float = 3.0):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })

    def extract_title(self, html_text: str) -> Optional[str]:
        """Extracts HTML <title> safely."""
        match = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.IGNORECASE | re.DOTALL)
        if match:
            raw_title = match.group(1).strip()
            # Clean newlines and HTML entities
            cleaned = " ".join(raw_title.split())
            return html.unescape(cleaned)
        return None

    def find_tplink_signatures(self, text: str) -> List[str]:
        """Checks text for known TP-Link identifiers."""
        matches = []
        for pattern in TPLINK_SIGNATURES:
            found = re.findall(pattern, text, re.IGNORECASE)
            if found:
                matches.append(found[0])
        return list(dict.fromkeys(matches))

    def detect_model_hint(self, text: str) -> Optional[str]:
        """Looks for specific TP-Link model numbers in text."""
        patterns = [
            r"\b(Archer\s+[A-Za-z0-9\+]+)\b",
            r"\b(Deco\s+[A-Za-z0-9]+)\b",
            r"\b(TL-WR[0-9A-Z]+)\b",
            r"\b(TL-WDR[0-9A-Z]+)\b",
            r"\b(TL-MR[0-9A-Z]+)\b",
            r"\b(TD-W[0-9A-Z]+)\b",
            r"\b(CPE[0-9]+)\b",
            r"\b(EAP[0-9]+)\b",
        ]
        for p in patterns:
            match = re.search(p, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def inspect_url(self, ip: str, port: int, protocol: str) -> Optional[AdminEndpointInfo]:
        """Tests a specific URL scheme (HTTP/HTTPS) and gathers public metadata."""
        url = f"{protocol}://{ip}:{port}/" if (protocol == "http" and port != 80) or (protocol == "https" and port != 443) else f"{protocol}://{ip}/"
        try:
            resp = self.session.get(
                url,
                timeout=self.timeout,
                verify=False,
                allow_redirects=True
            )

            redirects = [r.url for r in resp.history]
            final_url = resp.url
            server_header = resp.headers.get("Server", "")
            auth_realm = resp.headers.get("WWW-Authenticate", "")

            # Combine headers and initial body chunk for signature matching
            content_snippet = resp.text[:20000] if resp.text else ""
            inspect_blob = f"{server_header} {auth_realm} {content_snippet}"

            title = self.extract_title(content_snippet)
            signatures = self.find_tplink_signatures(inspect_blob)
            model_hint = self.detect_model_hint(inspect_blob)

            return AdminEndpointInfo(
                url=url,
                port=port,
                protocol=protocol,
                status_code=resp.status_code,
                title=title,
                server_header=server_header if server_header else None,
                redirect_chain=redirects,
                final_url=final_url,
                auth_realm=auth_realm if auth_realm else None,
                tplink_signatures_found=signatures,
                model_hint=model_hint
            )
        except requests.exceptions.RequestException as e:
            logger.debug(f"HTTP inspection failed for {url}: {e}")
            return None

    def inspect_host(self, ip: str, ports: Optional[List[int]] = None) -> List[AdminEndpointInfo]:
        """
        Inspects potential web endpoints on given ports.
        Defaults to testing standard 80 (HTTP) and 443 (HTTPS) if ports not specified.
        """
        target_ports = ports or [80, 443]
        results: List[AdminEndpointInfo] = []

        for port in target_ports:
            # Determine appropriate protocol
            protocols_to_try = []
            if port in (443, 8443):
                protocols_to_try = ["https"]
            elif port in (80, 8080):
                protocols_to_try = ["http"]
            else:
                protocols_to_try = ["http", "https"]

            for proto in protocols_to_try:
                info = self.inspect_url(ip, port, proto)
                if info:
                    results.append(info)
                    # If http worked on port 80 or https worked on 443, no need to retry other scheme on same port
                    break

        return results
