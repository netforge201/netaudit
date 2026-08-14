"""'netaudit diff' - compare two most recent device snapshots."""
from __future__ import annotations

from pathlib import Path

import typer

from netaudit.utils.formatting import console, err_console, print_json
from netaudit.utils.logging import get_logger
from netaudit.utils.validators import ValidationError, validate_target

log = get_logger("commands.diff")


def diff(
    target: str = typer.Argument(..., help="Device IP/hostname to diff"),
    directory: str = typer.Option("./snapshots", "--directory", help="Snapshot storage directory"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Diff the two most recent snapshots of TARGET."""
    from netaudit.snapshots.differ import diff_snapshots
    from netaudit.snapshots.manager import latest_snapshots, load_snapshot

    try:
        validate_target(target)
    except ValidationError as exc:
        err_console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=2)

    snaps = latest_snapshots(Path(directory), target, count=2)
    if len(snaps) < 2:
        err_console.print(
            f"[bold red]Error:[/bold red] Need at least 2 snapshots for '{target}' "
            f"to diff, found {len(snaps)}. Run 'netaudit snapshot {target}' first."
        )
        raise typer.Exit(code=1)

    new_path, old_path = snaps[0], snaps[1]
    old_files = load_snapshot(old_path)
    new_files = load_snapshot(new_path)

    result = diff_snapshots(old_path.name, old_files, new_path.name, new_files)

    if json_output:
        print_json(result)
        return

    console.print("\n[bold]Network State Diff[/bold]")
    console.rule(style="dim")
    console.print(f"Comparing [cyan]{old_path.name}[/cyan] -> [cyan]{new_path.name}[/cyan]\n")

    if not result.file_diffs:
        console.print("No changes detected.")
        return

    for file_diff in result.file_diffs:
        console.print(f"[bold]{file_diff.label}[/bold]")
        for line in file_diff.added:
            console.print(f"  [green]+ {line}[/green]")
        for line in file_diff.removed:
            console.print(f"  [red]- {line}[/red]")
        console.print()

    console.print("[bold]Summary:[/bold]")
    console.print(f"Added: {result.total_added}")
    console.print(f"Removed: {result.total_removed}")
    console.print(f"Changed: {result.total_changed}")
