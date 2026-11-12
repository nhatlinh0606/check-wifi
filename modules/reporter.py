#!/usr/bin/env python3
"""
Module: Reporter
Formats and exports discovery & identification results to CLI (Rich), JSON, and Plain Text.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .network_discovery import NetworkInterfaceInfo
from .router_identifier import RouterIdentificationResult


class DiscoveryReporter:
    """Handles presentation and file export of discovery reports."""

    def __init__(self, reports_dir: Optional[str] = None):
        self.console = Console()
        self.reports_dir = reports_dir or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "reports"
        )
        os.makedirs(self.reports_dir, exist_ok=True)

    def print_cli_summary(
        self,
        iface: Optional[NetworkInterfaceInfo],
        results: List[RouterIdentificationResult]
    ) -> None:
        """Renders rich colored terminal output."""
        # Header Panel
        if iface:
            info_text = (
                f"[bold cyan]Interface:[/bold cyan] {iface.name}\n"
                f"[bold cyan]Local IP:[/bold cyan] {iface.ip}\n"
                f"[bold cyan]Subnet:[/bold cyan] {iface.network}\n"
                f"[bold cyan]Default Gateway:[/bold cyan] {iface.gateway or 'None'}"
            )
        else:
            info_text = "[yellow]No network interface information available.[/yellow]"

        self.console.print(Panel(info_text, title="[bold green]Router Discovery Report[/bold green]", border_style="green"))

        # Candidate Routers Table
        table = Table(title="Discovered Network Devices & Router Candidates", border_style="blue")
        table.add_column("IP Address", style="cyan", justify="left")
        table.add_column("MAC Address", style="dim")
        table.add_column("Gateway", justify="center")
        table.add_column("Vendor", style="magenta")
        table.add_column("TP-Link Candidate", justify="center")
        table.add_column("Confidence", justify="center")
        table.add_column("Open Ports", style="yellow")
        table.add_column("Admin URL", style="green")

        for r in results:
            gw_str = "[bold green]YES[/bold green]" if r.is_gateway else "no"
            tplink_str = "[bold green]YES[/bold green]" if r.is_tplink_candidate else "[dim]No[/dim]"

            if r.confidence == "High":
                conf_badge = f"[bold green]High ({r.confidence_score}%)[/bold green]"
            elif r.confidence == "Medium":
                conf_badge = f"[bold yellow]Medium ({r.confidence_score}%)[/bold yellow]"
            elif r.confidence == "Low":
                conf_badge = f"[bold red]Low ({r.confidence_score}%)[/bold red]"
            else:
                conf_badge = f"[dim]None ({r.confidence_score}%)[/dim]"

            ports_str = ", ".join(map(str, r.open_ports)) if r.open_ports else "-"
            admin_url = r.admin_url or "-"

            table.add_row(
                r.ip,
                r.mac or "Unknown",
                gw_str,
                r.detected_vendor,
                tplink_str,
                conf_badge,
                ports_str,
                admin_url
            )

        self.console.print(table)

        # Highlight High / Medium Candidates
        tplink_candidates = [r for r in results if r.is_tplink_candidate]
        if tplink_candidates:
            self.console.print("\n[bold yellow]★ Detected TP-Link Device Details:[/bold yellow]")
            for c in tplink_candidates:
                ev_list = "\n".join([f"  • {e}" for e in c.evidence])
                body = (
                    f"[bold]IP:[/bold] {c.ip}  |  [bold]MAC:[/bold] {c.mac or 'N/A'}\n"
                    f"[bold]Confidence:[/bold] {c.confidence} ({c.confidence_score}%)\n"
                    f"[bold]Admin URL:[/bold] {c.admin_url or 'N/A'}\n"
                    f"[bold]Model Hint:[/bold] {c.model_hint or 'Standard TP-Link Firmware'}\n\n"
                    f"[bold]Evidence:[/bold]\n{ev_list}"
                )
                self.console.print(Panel(body, title=f"Candidate: {c.ip}", border_style="yellow"))
        else:
            self.console.print("\n[dim]No high/medium confidence TP-Link routers detected in this scan.[/dim]")

    def export_json(
        self,
        iface: Optional[NetworkInterfaceInfo],
        results: List[RouterIdentificationResult],
        file_path: Optional[str] = None
    ) -> str:
        """Exports full scan results to JSON format."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_path = file_path or os.path.join(self.reports_dir, f"discovery_{timestamp}.json")

        data = {
            "timestamp": datetime.now().isoformat(),
            "interface": iface.to_dict() if iface else None,
            "results_count": len(results),
            "results": [r.to_dict() for r in results]
        }

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return target_path

    def export_txt(
        self,
        iface: Optional[NetworkInterfaceInfo],
        results: List[RouterIdentificationResult],
        file_path: Optional[str] = None
    ) -> str:
        """Exports clean plain text report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_path = file_path or os.path.join(self.reports_dir, f"discovery_{timestamp}.txt")

        lines = [
            "Router Discovery Report",
            "-----------------------",
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Interface: {iface.name if iface else 'N/A'}",
            f"Local IP: {iface.ip if iface else 'N/A'}",
            f"Subnet: {iface.network if iface else 'N/A'}",
            f"Default Gateway: {iface.gateway if iface else 'N/A'}",
            "",
            "Discovered Devices:",
            "-------------------"
        ]

        for r in results:
            lines.extend([
                f"Device: {r.ip}",
                f"  MAC: {r.mac or 'Unknown'}",
                f"  Vendor: {r.detected_vendor}",
                f"  Is Gateway: {r.is_gateway}",
                f"  Is TP-Link Candidate: {r.is_tplink_candidate}",
                f"  Confidence: {r.confidence} ({r.confidence_score}%)",
                f"  Open Ports: {', '.join(map(str, r.open_ports)) if r.open_ports else 'None'}",
                f"  Admin URL: {r.admin_url or 'None'}",
                f"  Model Hint: {r.model_hint or 'None'}",
                "  Evidence:"
            ])
            for ev in r.evidence:
                lines.append(f"    - {ev}")
            lines.append("")

        with open(target_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return target_path
