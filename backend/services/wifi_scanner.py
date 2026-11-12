"""
Service: Wi-Fi Scanner Service
Scans and discovers nearby wireless networks using standard Linux operating system APIs (nmcli).
Extracts SSID, BSSID, signal strength, channel, frequency, band, security protocol, encryption type, and vendor OUI.
Passive, read-only, non-intrusive.
"""

import logging
import re
import subprocess
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any

from modules.router_identifier import RouterIdentifier

logger = logging.getLogger(__name__)


@dataclass
class WifiNetwork:
    ssid: str
    bssid: str
    channel: int
    frequency: str
    band: str
    signal: int
    bars: str
    security: str
    encryption: str
    vendor: str
    is_connected: bool
    is_tplink: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class WifiScannerService:
    """Discovers nearby wireless access points and parses physical/radio telemetry."""

    def __init__(self):
        self.router_identifier = RouterIdentifier()

    def scan(self, rescan: bool = True) -> List[WifiNetwork]:
        """
        Scans nearby Wi-Fi access points via nmcli.
        """
        cmd = [
            "nmcli", "-t", "-f",
            "IN-USE,SSID,BSSID,MODE,CHAN,FREQ,RATE,SIGNAL,BARS,SECURITY",
            "dev", "wifi", "list"
        ]
        if rescan:
            cmd.extend(["--rescan", "yes"])

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10, check=False)
            if res.returncode != 0:
                logger.warning(f"nmcli wifi scan returned code {res.returncode}: {res.stderr}")
                return []
            return self.parse_nmcli_output(res.stdout)
        except Exception as e:
            logger.error(f"Error scanning Wi-Fi networks: {e}")
            return []

    def parse_nmcli_output(self, output: str) -> List[WifiNetwork]:
        networks: List[WifiNetwork] = []
        seen_bssids = set()

        for line in output.strip().splitlines():
            if not line.strip():
                continue

            # nmcli escapes colons in BSSIDs as '\:'
            marker = "___COLON___"
            safe_line = line.replace(r"\:", marker)
            raw_parts = safe_line.split(":")
            parts = [p.replace(marker, ":").strip() for p in raw_parts]

            # Expected 10 fields: IN-USE, SSID, BSSID, MODE, CHAN, FREQ, RATE, SIGNAL, BARS, SECURITY
            if len(parts) >= 8:
                raw_in_use = parts[0]
                raw_ssid = parts[1]
                raw_bssid = parts[2]
                # parts[3] is MODE
                raw_chan = parts[4] if len(parts) > 4 else "0"
                raw_freq = parts[5] if len(parts) > 5 else ""
                # parts[6] is RATE
                raw_signal = parts[7] if len(parts) > 7 else "0"
                raw_bars = parts[8] if len(parts) > 8 else "____"
                raw_security = parts[9] if len(parts) > 9 else "Open"

                bssid = raw_bssid.upper()
                if not bssid or bssid in seen_bssids:
                    continue
                seen_bssids.add(bssid)

                is_connected = (raw_in_use == "*")
                ssid = raw_ssid if raw_ssid else "[Hidden Network]"

                try:
                    channel = int(raw_chan)
                except ValueError:
                    channel = 0

                try:
                    signal = int(raw_signal)
                except ValueError:
                    signal = 0

                freq_str = raw_freq if raw_freq else (f"{2407 + channel * 5} MHz" if channel <= 14 else "5000 MHz")
                band = "5 GHz" if channel > 14 or "5" in freq_str.split()[0][:1] else "2.4 GHz"

                # Parse security and encryption
                sec_upper = raw_security.upper()
                if not raw_security or sec_upper == "--" or sec_upper == "NONE":
                    security_protocol = "Open (None)"
                    encryption_type = "None"
                elif "WPA3" in sec_upper:
                    security_protocol = "WPA3-SAE"
                    encryption_type = "AES-CCMP / GCMP"
                elif "WPA2" in sec_upper:
                    security_protocol = "WPA2-Personal (PSK)"
                    encryption_type = "AES-CCMP"
                elif "WPA1" in sec_upper or "WPA" in sec_upper:
                    security_protocol = "WPA-Personal (PSK)"
                    encryption_type = "TKIP"
                elif "WEP" in sec_upper:
                    security_protocol = "WEP"
                    encryption_type = "RC4"
                else:
                    security_protocol = raw_security
                    encryption_type = "Standard"

                vendor = self.router_identifier.lookup_mac_vendor(bssid)
                is_tplink = (
                    "TP-LINK" in vendor.upper()
                    or bool(re.search(r"\b(tplink|tp-link|archer|deco)\b", ssid, re.I))
                )

                networks.append(
                    WifiNetwork(
                        ssid=ssid,
                        bssid=bssid,
                        channel=channel,
                        frequency=freq_str,
                        band=band,
                        signal=signal,
                        bars=raw_bars,
                        security=security_protocol,
                        encryption=encryption_type,
                        vendor=vendor,
                        is_connected=is_connected,
                        is_tplink=is_tplink
                    )
                )

        # Sort by signal strength descending
        return sorted(networks, key=lambda n: n.signal, reverse=True)

    def get_target_network(self, ssid: str, bssid: Optional[str] = None) -> Optional[WifiNetwork]:
        """Finds a specific network by SSID and optional BSSID."""
        networks = self.scan(rescan=False)
        target_ssid_clean = ssid.strip().lower()
        target_bssid_clean = bssid.strip().upper() if bssid else None

        for net in networks:
            if target_bssid_clean and net.bssid.upper() == target_bssid_clean:
                return net
            if net.ssid.lower() == target_ssid_clean:
                return net

        # Fallback dummy if offline or target out of range
        return None


wifi_scanner = WifiScannerService()
