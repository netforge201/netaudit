"""'netaudit snapshot' - capture and list device state snapshots.

Design note: this command intentionally does NOT use a Click/Typer
subcommand named 'list' alongside a default target-taking action.
Click's argument parser greedily consumes the first positional token
for the group's own 'target' argument before subcommand routing is
attempted, so 'netaudit snapshot list' would be silently parsed as
"snapshot a device named list" rather than dispatching to a 'list'
subcommand. Using a --list flag instead avoids that ambiguity
entirely. Verified against Click 8.3 directly.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.table import Table

from netaudit.utils.formatting import console, err_console, print_json
from netaudit.utils.logging import get_logger
from netaudit.utils.validators import ValidationError, validate_target

log = get_logger("commands.snapshot")


def snapshot(
    target: str | None = typer.Argument(
        None, help="Device IP/hostname to snapshot (omit when using --list)"
    ),
    list_snapshots_flag: bool = typer.Option(
        False, "--list", help="List saved snapshots instead of capturing a new one"
    ),
    username: str | None = typer.Option(None, "--username", envvar="NETAUDIT_USERNAME"),
    password: str | None = typer.Option(None, "--password", envvar="NETAUDIT_PASSWORD"),
    device_type: str = typer.Option("cisco_ios", "--device-type"),
    port: int = typer.Option(22, "--port"),
    directory: str = typer.Option("./snapshots", "--directory", help="Snapshot storage directory"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Capture a state snapshot of TARGET, or list saved snapshots with --list."""
    if list_snapshots_flag:
        _list_snapshots(target, directory, json_output)
        return

    if target is None:
        err_console.print(
            "[bold red]Error:[/bold red] TARGET is required (or use 'netaudit snapshot --list')."
        )
        raise typer.Exit(code=2)

    from netaudit.devices import module_for
    from netaudit.devices.connector import (
        DeviceAuthenticationError,
        DeviceConnectionError,
        MissingDependencyError,
        device_session,
        resolve_credentials,
    )
    from netaudit.snapshots.manager import create_snapshot

    try:
        validate_target(target)
    except ValidationError as exc:
        err_console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=2) from None

    try:
        creds = resolve_credentials(username, password)
        with device_session(target, device_type, creds, port=port) as conn:
            module = module_for(device_type)
            output = module.collect_info(conn)
    except MissingDependencyError as exc:
        err_console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from None
    except DeviceAuthenticationError as exc:
        err_console.print(f"[bold red]Authentication failed:[/bold red] {exc}")
        raise typer.Exit(code=4) from None
    except DeviceConnectionError as exc:
        err_console.print(f"[bold red]Connection failed:[/bold red] {exc}")
        raise typer.Exit(code=3) from None

    snap = create_snapshot(Path(directory), target, output)

    if json_output:
        print_json({"target": target, "timestamp": snap.timestamp, "path": str(snap.path)})
        return

    console.print(f"[bold green]Snapshot saved[/bold green]: {snap.path}")


def _list_snapshots(target: str | None, directory: str, json_output: bool) -> None:
    from netaudit.snapshots.manager import list_snapshots

    snaps = list_snapshots(Path(directory), target)

    if json_output:
        print_json([{"target": t, "timestamp": ts, "path": str(p)} for t, ts, p in snaps])
        return

    console.print("\n[bold]Saved Snapshots[/bold]")
    console.rule(style="dim")

    if not snaps:
        console.print("No snapshots found.")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("TARGET")
    table.add_column("TIMESTAMP")
    table.add_column("PATH")
    for t, ts, path in snaps:
        table.add_row(t, ts, str(path))
    console.print(table)
