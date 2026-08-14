"""'netaudit ports' - TCP port scanning against a single host."""
from __future__ import annotations

from typing import Optional

import typer
from rich.table import Table

from netaudit.utils.formatting import COMMON_TCP_PORTS, console, err_console, print_json
from netaudit.utils.logging import get_logger
from netaudit.utils.validators import ValidationError, parse_ports, validate_target

log = get_logger("commands.ports")


def ports(
    target: str = typer.Argument(..., help="IP address or hostname"),
    ports_opt: Optional[str] = typer.Option(
        None, "--ports", help="Comma-separated ports, e.g. 22,80,443"
    ),
    range_opt: Optional[str] = typer.Option(
        None, "--range", help="Port range, e.g. 1-1024"
    ),
    timeout: float = typer.Option(1.0, "--timeout", help="Per-port timeout in seconds"),
    workers: int = typer.Option(100, "--workers", help="Concurrent worker threads"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    csv_output: bool = typer.Option(False, "--csv", help="Output as CSV"),
):
    """Scan TCP ports on TARGET."""
    from netaudit.scanner.tcp import scan_ports

    try:
        validate_target(target)
    except ValidationError as exc:
        err_console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=2)

    spec = ports_opt or range_opt
    try:
        port_list = parse_ports(spec).ports if spec else list(COMMON_TCP_PORTS)
    except ValidationError as exc:
        err_console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=2)

    results = scan_ports(target, port_list, timeout=timeout, workers=workers)

    if json_output:
        print_json({
            "target": target,
            "ports": [{"port": r.port, "state": r.state, "service": r.service} for r in results],
        })
        return

    if csv_output:
        import csv as csv_module
        import sys

        writer = csv_module.writer(sys.stdout)
        writer.writerow(["port", "state", "service"])
        for r in results:
            writer.writerow([r.port, r.state, r.service])
        return

    console.print(f"\n[bold]Port scan: {target}[/bold]")
    console.rule(style="dim")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("PORT")
    table.add_column("STATE")
    table.add_column("SERVICE")
    for r in results:
        style = {"open": "green", "closed": "red dim", "filtered": "yellow"}[r.state]
        table.add_row(str(r.port), f"[{style}]{r.state.upper()}[/{style}]", r.service)
    console.print(table)

    open_count = sum(1 for r in results if r.state == "open")
    console.print(f"\n[bold]{open_count}[/bold] open / [bold]{len(results)}[/bold] scanned")
