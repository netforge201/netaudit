"""'netaudit interfaces' - local network interface listing."""

from __future__ import annotations

import typer
from rich.table import Table

from netaudit.utils.formatting import console, print_json
from netaudit.utils.logging import get_logger

log = get_logger("commands.interfaces")


def interfaces(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List local network interfaces and their addresses/counters."""
    from netaudit.network.interfaces import list_interfaces

    ifaces = list_interfaces()

    if json_output:
        print_json(ifaces)
        return

    console.print("\n[bold]Local Network Interfaces[/bold]")
    console.rule(style="dim")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("INTERFACE")
    table.add_column("STATE")
    table.add_column("MAC")
    table.add_column("IPv4")
    table.add_column("IPv6")
    table.add_column("MTU")
    table.add_column("RX")
    table.add_column("TX")

    for iface in ifaces:
        state_style = "green" if iface.is_up else "red dim"
        table.add_row(
            iface.name,
            f"[{state_style}]{'UP' if iface.is_up else 'DOWN'}[/{state_style}]",
            iface.mac or "—",
            ", ".join(iface.ipv4) or "—",
            ", ".join(iface.ipv6) or "—",
            str(iface.mtu) if iface.mtu else "—",
            f"{iface.bytes_recv:,}" if iface.bytes_recv is not None else "—",
            f"{iface.bytes_sent:,}" if iface.bytes_sent is not None else "—",
        )
    console.print(table)
