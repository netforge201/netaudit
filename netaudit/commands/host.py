"""'netaudit host' - detailed information about a single host."""
from __future__ import annotations

import contextlib

import typer
from rich.table import Table

from netaudit.utils.formatting import console, err_console, print_json
from netaudit.utils.logging import get_logger
from netaudit.utils.validators import ValidationError, validate_target

log = get_logger("commands.host")


def host(
    target: str = typer.Argument(..., help="IP address or hostname"),
    timeout: float = typer.Option(2.0, "--timeout", help="Timeout in seconds"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Show reachability, DNS, MAC/vendor, and open-port details for TARGET."""
    import socket

    from netaudit.network.dns import DnsLookupError, reverse_lookup
    from netaudit.scanner.arp import SCAPY_AVAILABLE, lookup_mac
    from netaudit.scanner.discovery import vendor_from_mac
    from netaudit.scanner.icmp import os_hint_from_ttl, ping
    from netaudit.scanner.tcp import scan_ports
    from netaudit.utils.formatting import COMMON_TCP_PORTS

    try:
        validate_target(target)
    except ValidationError as exc:
        err_console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=2) from None

    # Resolve to IP if a hostname was given
    try:
        ip = socket.gethostbyname(target)
    except socket.gaierror as exc:
        err_console.print(f"[bold red]Error:[/bold red] Could not resolve '{target}': {exc}")
        raise typer.Exit(code=3) from None

    ping_result = ping(ip, count=4, timeout=timeout)

    hostname = None
    with contextlib.suppress(DnsLookupError):
        hostname = reverse_lookup(ip, timeout=timeout)

    mac = lookup_mac(ip, timeout=timeout) if SCAPY_AVAILABLE else None
    vendor = vendor_from_mac(mac)

    port_results = scan_ports(ip, COMMON_TCP_PORTS, timeout=min(timeout, 1.5), workers=20)
    open_ports = [p for p in port_results if p.state == "open"]

    data = {
        "ip": ip,
        "queried_as": target,
        "hostname": hostname,
        "reachable": ping_result.reachable,
        "latency_ms": ping_result.avg_ms,
        "packet_loss_pct": ping_result.packet_loss_pct,
        "ttl": ping_result.ttl,
        "os_hint": os_hint_from_ttl(ping_result.ttl),
        "mac": mac,
        "vendor": vendor,
        "mac_lookup_available": SCAPY_AVAILABLE,
        "open_ports": [{"port": p.port, "service": p.service} for p in open_ports],
    }

    if json_output:
        print_json(data)
        return

    console.print(f"\n[bold]Host details: {target}[/bold]")
    console.rule(style="dim")

    table = Table(show_header=False, box=None)
    table.add_column(style="bold")
    table.add_column()
    table.add_row("IP", ip)
    table.add_row("Hostname (rDNS)", hostname or "—")
    status_style = "green" if ping_result.reachable else "red"
    table.add_row("Reachable", f"[{status_style}]{ping_result.reachable}[/{status_style}]")
    table.add_row("Latency", f"{ping_result.avg_ms} ms" if ping_result.avg_ms else "—")
    table.add_row("Packet loss", f"{ping_result.packet_loss_pct}%")
    table.add_row("TTL", str(ping_result.ttl) if ping_result.ttl is not None else "—")
    table.add_row("OS hint", os_hint_from_ttl(ping_result.ttl) or "—")
    table.add_row("MAC", mac or ("unavailable" if not SCAPY_AVAILABLE else "no reply"))
    table.add_row("Vendor", vendor or "—")
    console.print(table)

    console.print("\n[bold]Open ports:[/bold]")
    if open_ports:
        port_table = Table(show_header=True, header_style="bold cyan")
        port_table.add_column("PORT")
        port_table.add_column("SERVICE")
        for p in open_ports:
            port_table.add_row(str(p.port), p.service)
        console.print(port_table)
    else:
        console.print("  none detected among common ports")

    if not SCAPY_AVAILABLE:
        err_console.print(
            "\n[yellow]Note:[/yellow] MAC address lookup unavailable "
            "(scapy not installed or insufficient privileges)."
        )
