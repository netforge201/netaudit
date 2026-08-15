"""'netaudit ping' - ICMP reachability check."""

from __future__ import annotations

import typer

from netaudit.utils.formatting import console, err_console, print_json
from netaudit.utils.logging import get_logger
from netaudit.utils.validators import ValidationError, validate_target

log = get_logger("commands.ping")


def ping(
    target: str = typer.Argument(..., help="IP address or hostname"),
    count: int = typer.Option(4, "--count", help="Number of packets to send"),
    timeout: float = typer.Option(2.0, "--timeout", help="Per-packet timeout in seconds"),
    interval: float = typer.Option(1.0, "--interval", help="Interval between packets in seconds"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Ping TARGET and report round-trip statistics."""
    from netaudit.scanner.icmp import ping as do_ping

    try:
        validate_target(target)
    except ValidationError as exc:
        err_console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=2) from None

    result = do_ping(target, count=count, timeout=timeout, interval=interval)

    if json_output:
        print_json(result)
        if not result.reachable:
            raise typer.Exit(code=3) from None
        return

    console.print(f"\n[bold]PING {target}[/bold]\n")
    for t in result.raw_times_ms:
        console.print(f"64 bytes from {target}: time={t} ms")
    if not result.raw_times_ms and result.error:
        err_console.print(f"[red]{result.error}[/red]")

    console.print(f"\n[bold]Packets:[/bold] {result.packets_sent}")
    console.print(f"[bold]Received:[/bold] {result.packets_received}")
    loss_style = "green" if result.packet_loss_pct == 0 else "red"
    console.print(f"[bold]Loss:[/bold] [{loss_style}]{result.packet_loss_pct}%[/{loss_style}]")
    if result.min_ms is not None:
        console.print(f"[bold]Min:[/bold] {result.min_ms} ms")
        console.print(f"[bold]Avg:[/bold] {result.avg_ms} ms")
        console.print(f"[bold]Max:[/bold] {result.max_ms} ms")

    if not result.reachable:
        raise typer.Exit(code=3) from None
