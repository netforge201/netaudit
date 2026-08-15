"""'netaudit route' - traceroute to a target."""
from __future__ import annotations

import typer
from rich.table import Table

from netaudit.utils.formatting import console, err_console, print_json
from netaudit.utils.logging import get_logger
from netaudit.utils.validators import ValidationError, validate_target

log = get_logger("commands.route")


def route(
    target: str = typer.Argument(..., help="IP address or hostname"),
    max_hops: int = typer.Option(30, "--max-hops", help="Maximum number of hops"),
    timeout: float = typer.Option(2.0, "--timeout", help="Per-hop timeout in seconds"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Trace the network route to TARGET."""
    from netaudit.network.routing import traceroute

    try:
        validate_target(target)
    except ValidationError as exc:
        err_console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=2) from None

    result = traceroute(target, max_hops=max_hops, timeout=timeout)

    if result.error and not result.hops:
        if json_output:
            print_json({"target": target, "error": result.error})
        else:
            err_console.print(f"[bold red]Error:[/bold red] {result.error}")
        raise typer.Exit(code=3) from None

    if json_output:
        print_json(result)
        return

    console.print(f"\n[bold]Traceroute to {target}[/bold]\n")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("HOP")
    table.add_column("ADDRESS")
    table.add_column("RTT")
    for hop in result.hops:
        rtt = ", ".join(f"{t} ms" for t in hop.rtt_ms) if hop.rtt_ms else "*"
        address = hop.address or "*"
        table.add_row(str(hop.number), address, rtt)
    console.print(table)

    if result.reached:
        console.print("\n[green]Destination reached.[/green]")
    else:
        console.print(f"\n[yellow]Destination not confirmed within {max_hops} hops.[/yellow]")
