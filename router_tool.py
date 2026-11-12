#!/usr/bin/env python3
"""
TP-Link Router Discovery & Recovery Toolkit
A modular, non-intrusive administration and diagnostic tool for discovering,
identifying, and recovering access to TP-Link routers on Ubuntu Linux.
"""

import argparse
import logging
import os
import sys
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler

# Local modules
from modules.network_discovery import NetworkDiscovery
from modules.arp_scanner import ArpScanner
from modules.port_scanner import PortScanner
from modules.admin_interface import AdminInterfaceInspector
from modules.router_identifier import RouterIdentifier
from modules.recovery_assistant import RecoveryAssistant
from modules.reporter import DiscoveryReporter

console = Console()


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True, show_path=False)]
    )


def cmd_discover(args):
    """Executes full discovery, scanning, port checks, and router identification."""
    console.print("[bold green]Starting Network Discovery & Router Identification...[/bold green]")
    net_disc = NetworkDiscovery(interface=args.interface)
    iface_info = net_disc.get_active_interface()

    if not iface_info:
        console.print("[bold red]Error: No active network interface detected.[/bold red]")
        sys.exit(1)

    console.print(f"[cyan]Active Interface:[/cyan] {iface_info.name} ([dim]{iface_info.ip}[/dim])")
    console.print(f"[cyan]Target Subnet:[/cyan] {iface_info.network}")
    console.print(f"[cyan]Default Gateway:[/cyan] {iface_info.gateway or 'None'}")

    arp_scanner = ArpScanner(interface=args.interface)
    console.print("[yellow]Discovering active hosts in subnet...[/yellow]")
    hosts = arp_scanner.scan_subnet(subnet_cidr=args.subnet or iface_info.network)
    console.print(f"Found [bold cyan]{len(hosts)}[/bold cyan] active host(s).")

    router_id = RouterIdentifier()
    results = []
    with console.status("[bold green]Inspecting candidate devices...[/bold green]"):
        for h in hosts:
            res = router_id.identify_device(
                ip=h.ip,
                mac=h.mac,
                is_gateway=h.is_gateway,
                scan_ports=True,
                inspect_web=True
            )
            results.append(res)

    reporter = DiscoveryReporter()
    reporter.print_cli_summary(iface_info, results)

    # Optional auto export
    if getattr(args, "report_format", None):
        if args.report_format == "json":
            out_file = reporter.export_json(iface_info, results, args.output)
            console.print(f"[green]JSON report saved to:[/green] {out_file}")
        elif args.report_format == "txt":
            out_file = reporter.export_txt(iface_info, results, args.output)
            console.print(f"[green]Text report saved to:[/green] {out_file}")


def cmd_scan(args):
    """Scans subnet for live hosts."""
    console.print("[bold green]Subnet Host Scanner[/bold green]")
    net_disc = NetworkDiscovery(interface=args.interface)
    iface = net_disc.get_active_interface()

    subnet = args.subnet or (iface.network if iface else None)
    if not subnet:
        console.print("[bold red]Error: Subnet could not be determined. Use --subnet option.[/bold red]")
        sys.exit(1)

    arp_scanner = ArpScanner(interface=args.interface)
    hosts = arp_scanner.scan_subnet(subnet_cidr=subnet)

    from rich.table import Table
    table = Table(title=f"Live Hosts in {subnet}", border_style="cyan")
    table.add_column("IP Address", style="cyan")
    table.add_column("MAC Address", style="dim")
    table.add_column("Gateway", justify="center")
    table.add_column("Hostname", style="green")

    for h in hosts:
        gw_str = "[bold green]YES[/bold green]" if h.is_gateway else "no"
        table.add_row(h.ip, h.mac or "Unknown", gw_str, h.hostname or "-")

    console.print(table)


def cmd_identify(args):
    """Performs deep identification on a specific IP."""
    target_ip = args.ip
    console.print(f"[bold green]Identifying Device:[/bold green] {target_ip}")

    # Look up MAC from ARP table if not provided
    net_disc = NetworkDiscovery()
    arp_entries = net_disc.get_arp_table()
    mac = None
    for entry in arp_entries:
        if entry["ip"] == target_ip:
            mac = entry["mac"]
            break

    default_route = net_disc.get_default_gateway()
    is_gateway = bool(default_route and default_route.get("gateway") == target_ip)

    router_id = RouterIdentifier()
    with console.status(f"Inspecting {target_ip}..."):
        res = router_id.identify_device(
            ip=target_ip,
            mac=mac,
            is_gateway=is_gateway,
            scan_ports=True,
            inspect_web=True
        )

    reporter = DiscoveryReporter()
    reporter.print_cli_summary(net_disc.get_active_interface(), [res])


def cmd_inspect(args):
    """Detailed web inspection of admin interface for a specific IP."""
    target_ip = args.ip
    console.print(f"[bold green]Inspecting Web Admin Interface:[/bold green] {target_ip}")

    port_scanner = PortScanner()
    console.print("[yellow]Checking common web ports...[/yellow]")
    port_results = port_scanner.scan_host(target_ip)
    open_ports = [p.port for p in port_results if p.is_open]

    inspector = AdminInterfaceInspector()
    endpoints = inspector.inspect_host(target_ip, ports=open_ports or [80, 443])

    if not endpoints:
        console.print(f"[red]No responding HTTP/HTTPS admin endpoints found on {target_ip}.[/red]")
        return

    from rich.panel import Panel
    for ep in endpoints:
        details = (
            f"[bold]URL:[/bold] {ep.url}\n"
            f"[bold]Final URL:[/bold] {ep.final_url}\n"
            f"[bold]Status Code:[/bold] {ep.status_code}\n"
            f"[bold]Title:[/bold] {ep.title or 'N/A'}\n"
            f"[bold]Server Header:[/bold] {ep.server_header or 'N/A'}\n"
            f"[bold]Auth Realm:[/bold] {ep.auth_realm or 'None'}\n"
            f"[bold]TP-Link Signatures:[/bold] {', '.join(ep.tplink_signatures_found) if ep.tplink_signatures_found else 'None'}\n"
            f"[bold]Model Hint:[/bold] {ep.model_hint or 'None'}\n"
            f"[bold]Redirect Chain:[/bold] {' -> '.join(ep.redirect_chain) if ep.redirect_chain else 'Direct'}"
        )
        console.print(Panel(details, title=f"Endpoint: {ep.protocol.upper()} (Port {ep.port})", border_style="cyan"))


def cmd_assist(args):
    """Launches Recovery Assistant."""
    assistant = RecoveryAssistant()
    if args.case:
        assistant.print_case(args.case)
    else:
        assistant.interactive_menu()


def cmd_report(args):
    """Generates and exports discovery report."""
    args.report_format = args.format
    cmd_discover(args)


def main():
    parser = argparse.ArgumentParser(
        description="TP-Link Router Discovery & Recovery Toolkit (Ubuntu Linux)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 router_tool.py discover
  python3 router_tool.py scan --interface enp3s0
  python3 router_tool.py identify --ip 192.168.1.1
  python3 router_tool.py inspect --ip 192.168.1.1
  python3 router_tool.py assist --case E
  python3 router_tool.py report --format json
"""
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose debug logging")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: discover
    p_discover = subparsers.add_parser("discover", help="Discover devices, scan ports, and identify TP-Link routers")
    p_discover.add_argument("-i", "--interface", help="Target network interface (e.g. enp3s0, wlp0s20f3)")
    p_discover.add_argument("-s", "--subnet", help="Custom subnet CIDR (e.g. 192.168.1.0/24)")
    p_discover.add_argument("--format", choices=["json", "txt"], dest="report_format", help="Export report format")
    p_discover.add_argument("-o", "--output", help="Custom report output file path")
    p_discover.set_defaults(func=cmd_discover)

    # Command: scan
    p_scan = subparsers.add_parser("scan", help="Scan subnet for active IP and MAC addresses")
    p_scan.add_argument("-i", "--interface", help="Target network interface")
    p_scan.add_argument("-s", "--subnet", help="Subnet CIDR to scan")
    p_scan.set_defaults(func=cmd_scan)

    # Command: identify
    p_identify = subparsers.add_parser("identify", help="Deep identification of a target IP")
    p_identify.add_argument("--ip", required=True, help="Target device IP address")
    p_identify.set_defaults(func=cmd_identify)

    # Command: inspect
    p_inspect = subparsers.add_parser("inspect", help="Inspect web management interface of a target IP")
    p_inspect.add_argument("--ip", required=True, help="Target device IP address")
    p_inspect.set_defaults(func=cmd_inspect)

    # Command: assist
    p_assist = subparsers.add_parser("assist", help="Interactive Recovery Assistant for forgotten credentials/reset")
    p_assist.add_argument("--case", choices=["A", "B", "C", "D", "E", "a", "b", "c", "d", "e"], help="Specific case (A-E)")
    p_assist.set_defaults(func=cmd_assist)

    # Command: report
    p_report = subparsers.add_parser("report", help="Generate and export discovery report")
    p_report.add_argument("--format", choices=["json", "txt"], default="json", help="Report format (json or txt)")
    p_report.add_argument("-i", "--interface", help="Target network interface")
    p_report.add_argument("-s", "--subnet", help="Subnet CIDR")
    p_report.add_argument("-o", "--output", help="Output file path")
    p_report.set_defaults(func=cmd_report)

    args = parser.parse_args()
    setup_logging(args.verbose)

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
