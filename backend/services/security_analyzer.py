"""
Service: Security Protocol & Interface Capabilities Analyzer
Evaluates target 802.11 security architecture (WPA/WPA2/WPA3), key derivation mechanics,
and local wireless interface hardware capabilities.
"""

import logging
import os
import subprocess
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class SecurityAnalyzerService:
    """Analyzes target Wi-Fi security protocols and hardware interface capabilities."""

    @classmethod
    def analyze_target(
        cls,
        ssid: str,
        bssid: Optional[str],
        security: str,
        encryption: str,
        channel: int,
        frequency: str,
        band: str
    ) -> Dict[str, Any]:
        sec_upper = security.upper()

        if "WPA3" in sec_upper:
            protocol_name = "WPA3-Personal"
            akm = "Simultaneous Authentication of Equals (SAE - RFC 7664)"
            cipher = "AES-CCMP-128 / GCMP-256"
            pmk_derivation = "Dragonfly handshake with zero-knowledge password proof"
            passive_crackable = False
            security_level = "High"
        elif "WPA2" in sec_upper:
            protocol_name = "WPA2-Personal (802.11i)"
            akm = "Pre-Shared Key (PSK)"
            cipher = "AES-CCMP"
            pmk_derivation = "PBKDF2-HMAC-SHA1 (4096 iterations of Passphrase + SSID salt)"
            passive_crackable = False
            security_level = "Standard"
        elif "WPA" in sec_upper:
            protocol_name = "WPA-Personal"
            akm = "Pre-Shared Key (PSK)"
            cipher = "TKIP (RC4 with Michael MIC)"
            pmk_derivation = "PBKDF2-HMAC-SHA1 (4096 iterations)"
            passive_crackable = False
            security_level = "Legacy / Deprecated"
        elif "WEP" in sec_upper:
            protocol_name = "WEP (Wired Equivalent Privacy)"
            akm = "Shared Key / Open"
            cipher = "RC4 (64-bit / 128-bit static key)"
            pmk_derivation = "Static IV key stream"
            passive_crackable = True
            security_level = "Insecure"
        else:
            protocol_name = "Open (Unencrypted)"
            akm = "None"
            cipher = "None"
            pmk_derivation = "None"
            passive_crackable = False
            security_level = "None"

        # Hardware interface status
        iface_info = cls._get_wireless_interface_telemetry()

        return {
            "target_ssid": ssid,
            "target_bssid": bssid,
            "protocol_name": protocol_name,
            "akm_suite": akm,
            "pairwise_cipher": cipher,
            "pmk_derivation": pmk_derivation,
            "frequency_band": f"{band} ({frequency})",
            "channel": channel,
            "security_level": security_level,
            "passive_airwave_extraction_possible": False,
            "technical_limitation_explanation": (
                "Under the IEEE 802.11i specification, beacon management frames broadcast in the clear "
                "contain only the RSN Information Element (advertising supported ciphers and AKM suites). "
                "The pre-shared passphrase is never transmitted over the air. "
                "Legitimate password recovery can only be performed via authorized local storage, "
                "router configuration archives, or physical equipment access."
            ),
            "interface_telemetry": iface_info,
        }

    @staticmethod
    def _get_wireless_interface_telemetry() -> Dict[str, str]:
        """Inspects active wireless device and driver via sysfs."""
        sysfs_net = "/sys/class/net"
        if os.path.exists(sysfs_net):
            for iface in os.listdir(sysfs_net):
                if iface.startswith(("wl", "wlan", "wifi")):
                    dev_path = os.path.join(sysfs_net, iface, "device")
                    driver = "Standard cfg80211 / nl80211 driver"
                    pci_id = "Integrated"
                    if os.path.exists(dev_path):
                        uevent = os.path.join(dev_path, "uevent")
                        if os.path.exists(uevent):
                            try:
                                with open(uevent, "r") as f:
                                    for line in f:
                                        if line.startswith("DRIVER="):
                                            driver = line.strip().split("=")[1]
                                        elif line.startswith("PCI_ID="):
                                            pci_id = line.strip().split("=")[1]
                            except Exception:
                                pass
                    return {
                        "interface": iface,
                        "driver": driver,
                        "pci_id": pci_id,
                        "type": "Wireless Network Interface Controller (WNIC)"
                    }
        return {
            "interface": "wlan0 (generic)",
            "driver": "nl80211",
            "pci_id": "Integrated",
            "type": "Wireless Controller"
        }


security_analyzer = SecurityAnalyzerService()
