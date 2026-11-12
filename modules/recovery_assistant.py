#!/usr/bin/env python3
"""
Module: Recovery Assistant
Provides structured, scenario-based recovery guidance for TP-Link routers without
performing intrusive attacks or unauthorized configuration changes.
Covers Case A through Case E and includes model-specific hardware advice.
"""

from typing import Dict, List, Optional, Any
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown


RECOVERY_CASES: Dict[str, Dict[str, Any]] = {
    "A": {
        "title": "Case A: Web Admin Interface Reachable, but Password Unknown",
        "summary": "The web management page is accessible (e.g. at 192.168.0.1 or 192.168.1.1), but the administrator password has been changed or forgotten.",
        "steps": [
            "1. Check Default Credentials by Model:",
            "   - Older TL-WR models (e.g., TL-WR841N, TL-WR940N): Username 'admin', Password 'admin'.",
            "   - Newer Archer / Deco models: Do NOT have a default password; they prompt you to create a new password on initial setup.",
            "2. Utilize the 'Forgot Password?' Feature:",
            "   - On newer TP-Link web interfaces, click 'Forgot Password?'.",
            "   - If previously bound to a recovery email or TP-Link ID, a verification code will be sent to the owner's mailbox.",
            "3. Try the Official TP-Link Tether App:",
            "   - Download the TP-Link Tether app on your smartphone while connected to the same LAN (via Ethernet adapter or active Wi-Fi).",
            "   - If your smartphone previously managed this device via TP-Link Cloud ID, you may regain access or update credentials directly through the app without entering the local admin password.",
            "4. Check for Saved Browser Credentials:",
            "   - Check saved passwords in Google Chrome, Firefox, or Safari on computers previously used to configure this router.",
            "5. If all credentials fail: See Case E for the Physical Reset procedure."
        ]
    },
    "B": {
        "title": "Case B: Admin IP Address Found, but No Credentials",
        "summary": "Network discovery identified the router's IP and open ports (e.g., 80, 443), but login is blocked or unknown.",
        "steps": [
            "1. Verify Admin URL and Protocol:",
            "   - Test both HTTP (http://<IP>) and HTTPS (https://<IP>) in case automatic redirection is failing.",
            "   - Check alternate ports: 8080 (http://<IP>:8080) or 8443 (https://<IP>:8443).",
            "   - Use Incognito / Private Browsing to avoid cached sessions or corrupted cookies.",
            "2. Access via TP-Link Domain Names:",
            "   - Many TP-Link routers intercept local DNS for: http://tplinkwifi.net or http://tplinklogin.net.",
            "3. Check for Open SSH / Telnet (Port 22/23):",
            "   - If ports 22 or 23 are open, note that stock TP-Link firmware disables shell access, but ISP-customized or OpenWrt firmware may provide recovery console access.",
            "4. If no recovery channel is available: Physical Factory Reset (Case E) is the standard and safest path."
        ]
    },
    "C": {
        "title": "Case C: Router Admin IP Not Found in Current Subnet",
        "summary": "The computer is on a subnet (e.g. 192.168.1.x), but the target TP-Link router is not visible or operates as an Access Point (AP) / Secondary Router with a different subnet.",
        "steps": [
            "1. Direct Physical Ethernet Connection:",
            "   - Connect an RJ45 Ethernet cable directly from the Ubuntu PC into one of the LAN ports (often yellow) on the TP-Link router.",
            "   - Disconnect other Wi-Fi networks to prevent IP conflicts.",
            "2. Check DHCP Auto-Assignment on Ubuntu:",
            "   - Run: 'sudo dhclient -r && sudo dhclient <interface>' to request a fresh IP lease from the router's DHCP server.",
            "   - Run: 'ip route show default' to inspect the assigned gateway.",
            "3. Scan Alternative Default Subnets:",
            "   - TP-Link standard default subnets: 192.168.0.1/24, 192.168.1.1/24, 192.168.0.254/24 (CPE/Outdoor), 10.0.0.1/24.",
            "   - Temporarily assign an IP in the 192.168.0.x range to test:",
            "     'sudo ip addr add 192.168.0.100/24 dev <interface>'",
            "   - Then re-run: 'python3 router_tool.py scan --interface <interface> --subnet 192.168.0.0/24'.",
            "4. Identify Upstream Gateway vs Sub-Router:",
            "   - If your main gateway is from an ISP (e.g., ZTE/Huawei ONT), the TP-Link may be configured as a secondary AP. Check the client list on the main router to locate the TP-Link's assigned IP."
        ]
    },
    "D": {
        "title": "Case D: Computer Cannot Connect via Wi-Fi",
        "summary": "The Wi-Fi SSID password was modified or the signal is unreachable, preventing wireless communication.",
        "steps": [
            "1. Connect via Wired Ethernet Cable (Highest Reliability):",
            "   - Connect an Ethernet cable directly from your Ubuntu machine to a LAN port on the router or to a nearby network switch connected to it.",
            "   - Wired LAN connections do not require Wi-Fi passwords and provide direct, unhindered administrative access.",
            "2. Retrieve Saved Wi-Fi Passwords from Previously Connected Devices:",
            "   - On another Linux machine: 'sudo nmcli -s connection show <SSID> | grep 802-11-wireless-security.psk'",
            "   - On Windows: 'netsh wlan show profile name=\"<SSID>\" key=clear'",
            "   - On Android (Android 10+): Settings -> Network & Internet -> Internet -> Saved Networks -> Share (shows QR code & plain password).",
            "   - On iOS (iOS 16+): Settings -> Wi-Fi -> tap (i) icon -> tap 'Password' (Face ID / Touch ID reveals text).",
            "3. WPS Push Button Connection (if physically accessible):",
            "   - If WPS is enabled, pressing the WPS button on the router allows instant connection without typing the password."
        ]
    },
    "E": {
        "title": "Case E: Factory Reset Guide (Model-Specific Hardware Procedures)",
        "summary": "Complete instructions to restore router to original factory settings, wiping customized passwords and restoring default IP and setup wizard.",
        "steps": [
            "1. Outdoor / Pole-Mounted TP-Link Routers (CPE210, CPE510, EAP series):",
            "   - IMPORTANT FOR POLE-MOUNTED DEVICES: Check your indoor PoE Injector power supply!",
            "   - TP-Link PoE Injectors typically feature a dedicated 'Remote Reset' button directly on the indoor power adapter.",
            "   - Pressing and holding the 'Remote Reset' pinhole on the indoor PoE injector for ~10 seconds resets the outdoor device on the pole WITHOUT requiring physical climbing!",
            "   - Default management IP after reset: 192.168.0.254 (Subnet mask: 255.255.255.0). User/Pass: admin / admin.",
            "2. TP-Link Archer Series (Archer C6, C7, AX10, AX50, AX73, etc.):",
            "   - Ensure the router is powered ON.",
            "   - Locate the 'Reset' or 'WPS/Reset' pinhole button on the back panel.",
            "   - Use a paperclip or SIM ejector tool to press and hold the button for 8-10 seconds.",
            "   - Watch the LEDs: Release the button when all LEDs light up simultaneously or start flashing rapidly.",
            "   - Wait 1-2 minutes for the system reboot cycle.",
            "   - Default IP: 192.168.0.1 or http://tplinkwifi.net.",
            "   - Default Wi-Fi SSID and 8-digit PIN are printed on the product label underneath.",
            "3. TP-Link TL-WR Series (TL-WR841N, TL-WR940N, etc.):",
            "   - Power ON the router.",
            "   - Press and hold the WPS/Reset button for about 6-8 seconds until the SYS LED flashes rapidly.",
            "   - Default IP: 192.168.0.1 or 192.168.1.1. Default Login: admin / admin.",
            "4. TP-Link Deco Mesh Series:",
            "   - Press and hold the Reset button on the bottom of the Deco unit for 1 second.",
            "   - The LED will turn yellow, then pulse blue when ready for reconfiguration via the Deco app.",
            "5. Post-Reset Steps:",
            "   - Connect via Ethernet or default Wi-Fi SSID.",
            "   - Navigate to http://tplinkwifi.net in your browser.",
            "   - Follow the Quick Setup Wizard to set a new administrator password and secure Wi-Fi key."
        ]
    }
}


class RecoveryAssistant:
    """Provides structured troubleshooting workflows and actionable advice."""

    def __init__(self):
        self.console = Console()

    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves details for a specific case (A, B, C, D, E)."""
        return RECOVERY_CASES.get(case_id.upper())

    def print_case(self, case_id: str) -> None:
        """Displays formatted case instructions via Rich."""
        case_data = self.get_case(case_id)
        if not case_data:
            self.console.print(f"[bold red]Unknown recovery case: {case_id}[/bold red]")
            self.console.print("Valid cases are: [cyan]A, B, C, D, E[/cyan]")
            return

        title = f"[bold yellow]{case_data['title']}[/bold yellow]"
        body = f"[dim]{case_data['summary']}[/dim]\n\n" + "\n".join(case_data["steps"])
        self.console.print(Panel(body, title=title, expand=False, border_style="yellow"))

    def print_all_cases(self) -> None:
        """Displays summaries of all recovery scenarios."""
        self.console.print(Panel(
            "[bold white]TP-Link Router Recovery Assistant[/bold white]\n"
            "Select an appropriate recovery scenario below to view detailed, non-destructive step-by-step guidance:",
            title="Overview",
            border_style="cyan"
        ))
        for key, data in RECOVERY_CASES.items():
            self.console.print(f"[bold green]Case {key}:[/bold green] [bold]{data['title']}[/bold]")
            self.console.print(f"  [dim]{data['summary']}[/dim]\n")

    def interactive_menu(self) -> None:
        """Runs interactive CLI assistant."""
        self.print_all_cases()
        self.console.print("[cyan]Enter case letter (A-E) or 'q' to quit:[/cyan] ", end="")
        try:
            choice = input().strip().upper()
            if choice in RECOVERY_CASES:
                self.print_case(choice)
            elif choice == "Q":
                return
            else:
                self.console.print("[red]Invalid selection.[/red]")
        except (KeyboardInterrupt, EOFError):
            pass
