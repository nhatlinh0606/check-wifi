"""
Wi-Fi Service
Discovers nearby wireless access points using standard Linux OS APIs (nmcli).
Extracts SSID, BSSID, Signal strength, Channel, Security, Band, and Vendor OUI.
Strictly passive and read-only.
"""

import logging
import re
import subprocess
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any

from modules.router_identifier import RouterIdentifier

logger = logging.getLogger(__name__)


@dataclass
class WifiNetwork:
    ssid: str
    bssid: str
    channel: int
    signal: int
    bars: str
    security: str
    band: str
    vendor: str
    is_tplink: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class WifiService:
    def __init__(self):
        self.router_identifier = RouterIdentifier()

    def scan_networks(self, rescan: bool = True) -> List[WifiNetwork]:
        """
        Scans for visible Wi-Fi access points via nmcli.
        """
        cmd = ["nmcli", "-t", "-f", "SSID,BSSID,CHAN,BARS,SIGNAL,SECURITY", "dev", "wifi", "list"]
        if rescan:
            cmd.extend(["--rescan", "yes"])

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10, check=False)
            if res.returncode != 0:
                logger.warning(f"nmcli command returned error: {res.stderr}")
                return []
            return self._parse_nmcli_output(res.stdout)
        except Exception as e:
            logger.error(f"Error scanning Wi-Fi networks: {e}")
            return []

    def _parse_nmcli_output(self, output: str) -> List[WifiNetwork]:
        networks: List[WifiNetwork] = []
        seen_bssids = set()

        for line in output.strip().splitlines():
            if not line.strip():
                continue

            # nmcli escapes colons in BSSIDs with backslashes: e.g. 54\:04\:63\:23\:75\:31
            # Temporarily replace escaped colons
            escaped_marker = "__COLON__"
            safe_line = line.replace(r"\:", escaped_marker)
            parts = safe_line.split(":")

            if len(parts) >= 6:
                raw_ssid = parts[0].replace(escaped_marker, ":").strip()
                raw_bssid = parts[1].replace(escaped_marker, ":").strip()
                raw_chan = parts[2].replace(escaped_marker, ":").strip()
                raw_bars = parts[3].replace(escaped_marker, ":").strip()
                raw_signal = parts[4].replace(escaped_marker, ":").strip()
                raw_security = parts[5].replace(escaped_marker, ":").strip() if len(parts) > 5 else "None"

                ssid = raw_ssid if raw_ssid else "[Hidden SSID]"
                bssid = raw_bssid.upper()

                if bssid in seen_bssids:
                    continue
                seen_bssids.add(bssid)

                try:
                    channel = int(raw_chan)
                except ValueError:
                    channel = 0

                try:
                    signal = int(raw_signal)
                except ValueError:
                    signal = 0

                band = "2.4 GHz" if channel <= 14 else "5 GHz"
                vendor = self.router_identifier.lookup_mac_vendor(bssid)
                is_tplink = "TP-LINK" in vendor.upper() or bool(re.search(r"\b(tplink|tp-link|archer|deco)\b", ssid, re.I))

                networks.append(
                    WifiNetwork(
                        ssid=ssid,
                        bssid=bssid,
                        channel=channel,
                        signal=signal,
                        bars=raw_bars,
                        security=raw_security,
                        band=band,
                        vendor=vendor,
                        is_tplink=is_tplink
                    )
                )

        # Sort by signal strength descending
        return sorted(networks, key=lambda x: x.signal, reverse=True)

    def get_saved_profiles(self) -> List[Dict[str, str]]:
        """
        Lists saved Wi-Fi connections on the local machine via nmcli.
        """
        cmd = ["nmcli", "-t", "-f", "NAME,UUID,TYPE,DEVICE", "connection", "show"]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5, check=False)
            if res.returncode != 0:
                return []

            profiles = []
            for line in res.stdout.strip().splitlines():
                parts = line.split(":")
                if len(parts) >= 3 and "wireless" in parts[2]:
                    profiles.append({
                        "name": parts[0],
                        "uuid": parts[1],
                        "type": parts[2],
                        "active": bool(len(parts) > 3 and parts[3])
                    })
            return profiles
        except Exception as e:
            logger.error(f"Error fetching saved Wi-Fi profiles: {e}")
            return []
