"""'netaudit dns' - forward and reverse DNS lookups."""
from __future__ import annotations

import typer
from rich.table import Table

from netaudit.utils.formatting import console, err_console, print_json
from netaudit.utils.logging import get_logger

log = get_logger("commands.dns")


def dns(
    target: str = typer.Argument(..., help="Domain name (or IP with --reverse)"),
    reverse: bool = typer.Option(False, "--reverse", help="Perform a reverse (PTR) lookup"),
    timeout: float = typer.Option(3.0, "--timeout", help="Query timeout in seconds"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Query DNS records for TARGET."""
    from netaudit.network.dns import DnsLookupError, lookup, reverse_lookup

    if reverse:
        try:
            name = reverse_lookup(target, timeout=timeout)
        except DnsLookupError as exc:
            if json_output:
                print_json({"target": target, "error": str(exc)})
            else:
                err_console.print(f"[bold red]Error:[/bold red] {exc}")
            raise typer.Exit(code=3) from None

        if json_output:
            print_json({"target": target, "ptr": name})
            return
        console.print(f"\n[bold]Reverse DNS: {target}[/bold]")
        console.rule(style="dim")
        console.print(f"PTR  {name}")
        return

    records = lookup(target, timeout=timeout)

    if json_output:
        print_json(records)
        return

    console.print(f"\n[bold]DNS records: {target}[/bold]")
    console.rule(style="dim")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("TYPE")
    table.add_column("VALUE")
    for rtype in ("a", "aaaa", "cname", "mx", "ns", "txt"):
        values = getattr(records, rtype)
        for value in values:
            table.add_row(rtype.upper(), value)
    if table.row_count == 0:
        console.print("No records found.")
    else:
        console.print(table)

    if records.errors:
        for rtype, message in records.errors.items():
            err_console.print(f"[yellow]{rtype}:[/yellow] {message}")
