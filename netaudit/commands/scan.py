"""'netaudit scan' - network discovery over a CIDR range."""

from __future__ import annotations

import typer
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn
from rich.table import Table

from netaudit.utils.formatting import console, err_console, print_json
from netaudit.utils.logging import get_logger
from netaudit.utils.validators import ValidationError, parse_cidr, parse_ports

log = get_logger("commands.scan")


def scan(
    target: str = typer.Argument(..., help="CIDR network to scan, e.g. 192.168.1.0/24"),
    timeout: float = typer.Option(1.0, "--timeout", help="Per-host timeout in seconds"),
    workers: int = typer.Option(50, "--workers", help="Concurrent worker threads"),
    ports: str | None = typer.Option(
        None, "--ports", help="Also check these ports on live hosts, e.g. 22,80,443"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    csv_output: bool = typer.Option(False, "--csv", help="Output as CSV"),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress progress output"),
):
    """Discover live hosts on TARGET (a CIDR network)."""
    from netaudit.scanner.discovery import scan_network

    try:
        network = parse_cidr(target)
    except ValidationError as exc:
        err_console.print(
            f"Error: {exc}", markup=False, crop=False, overflow="ignore", no_wrap=True
        )
        raise typer.Exit(code=2) from None

    port_list = None
    if ports:
        try:
            port_list = parse_ports(ports).ports
        except ValidationError as exc:
            err_console.print(
                f"Error: {exc}", markup=False, crop=False, overflow="ignore", no_wrap=True
            )
            raise typer.Exit(code=2) from None

    show_progress = not quiet and not json_output and not csv_output

    if show_progress:
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task_id = progress.add_task("Scanning...", total=network.num_addresses)

            def on_progress(done: int, total: int) -> None:
                progress.update(task_id, completed=done, total=total)

            summary = scan_network(network, timeout, workers, port_list, on_progress)
    else:
        summary = scan_network(network, timeout, workers, port_list)

    if json_output:
        print_json(
            {
                "target": target,
                "hosts": summary.hosts,
                "discovered": summary.discovered,
                "online": summary.online,
                "offline": summary.offline,
                "duration_s": summary.duration_s,
            }
        )
        return

    if csv_output:
        import csv as csv_module
        import sys

        writer = csv_module.writer(sys.stdout)
        writer.writerow(["ip", "status", "latency_ms", "hostname", "mac", "vendor", "open_ports"])
        for host in summary.hosts:
            writer.writerow(
                [
                    host.ip,
                    host.status,
                    host.latency_ms or "",
                    host.hostname or "",
                    host.mac or "",
                    host.vendor or "",
                    ";".join(str(p.port) for p in host.open_ports),
                ]
            )
        return

    console.print("\n[bold]NetAudit Network Scan[/bold]")
    console.rule(style="dim")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("IP")
    table.add_column("STATUS")
    table.add_column("LATENCY")
    table.add_column("HOSTNAME")
    table.add_column("MAC")
    table.add_column("VENDOR")
    if port_list:
        table.add_column("OPEN PORTS")

    for host in summary.hosts:
        status_style = "green" if host.status == "up" else "red dim"
        latency = f"{host.latency_ms} ms" if host.latency_ms is not None else "—"
        hostname = host.hostname or "—"
        mac = host.mac or "—"
        vendor = host.vendor or "—"
        row = [
            host.ip,
            f"[{status_style}]{host.status.upper()}[/{status_style}]",
            latency,
            hostname,
            mac,
            vendor,
        ]
        if port_list:
            open_ports = ",".join(str(p.port) for p in host.open_ports) or "—"
            row.append(open_ports)
        table.add_row(*row)

    console.print(table)
    console.print()
    console.print(f"[bold]Hosts discovered:[/bold] {summary.discovered}")
    console.print(f"[bold green]Online:[/bold green] {summary.online}")
    console.print(f"[bold red]Offline:[/bold red] {summary.offline}")
    console.print(f"[bold]Duration:[/bold] {summary.duration_s}s")
