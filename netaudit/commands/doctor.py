"""'netaudit doctor' - comprehensive network/device health check."""
from __future__ import annotations

from typing import Optional

import typer

from netaudit.diagnostics.checks import CheckStatus
from netaudit.utils.formatting import console, err_console, print_json
from netaudit.utils.logging import get_logger
from netaudit.utils.validators import ValidationError, validate_target

log = get_logger("commands.doctor")

_STATUS_ICON = {
    CheckStatus.PASS: ("[green]\u2713[/green]", "green"),
    CheckStatus.WARN: ("[yellow]![/yellow]", "yellow"),
    CheckStatus.FAIL: ("[red]\u2717[/red]", "red"),
    CheckStatus.SKIP: ("[dim]-[/dim]", "dim"),
}


def doctor(
    target: str = typer.Argument(..., help="IP address or hostname to diagnose"),
    timeout: float = typer.Option(2.0, "--timeout", help="Per-check timeout in seconds"),
    device: bool = typer.Option(
        False, "--device", help="Also run device-level checks over SSH (requires credentials)"
    ),
    username: Optional[str] = typer.Option(None, "--username", envvar="NETAUDIT_USERNAME"),
    password: Optional[str] = typer.Option(None, "--password", envvar="NETAUDIT_PASSWORD"),
    device_type: str = typer.Option("cisco_ios", "--device-type"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Run a full health check against TARGET."""
    from netaudit.diagnostics.health import run_doctor

    try:
        validate_target(target)
    except ValidationError as exc:
        err_console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=2)

    credentials = None
    if device:
        from netaudit.devices.connector import resolve_credentials

        try:
            credentials = resolve_credentials(username, password, interactive=True)
        except Exception as exc:  # noqa: BLE001
            err_console.print(f"[yellow]Warning:[/yellow] {exc}. Skipping device checks.")

    report = run_doctor(
        target, timeout=timeout,
        device_type=device_type if device else None,
        credentials=credentials if device else None,
    )

    if json_output:
        print_json(report)
        return

    console.print("\n[bold]Network Health Check[/bold]")
    console.rule(style="dim")

    passing = [c for c in report.checks if c.status == CheckStatus.PASS]
    other = [c for c in report.checks if c.status != CheckStatus.PASS]

    for check in passing:
        icon, _ = _STATUS_ICON[check.status]
        console.print(f"{icon} {check.name}")

    if other:
        console.print()
    for check in other:
        icon, style = _STATUS_ICON[check.status]
        console.print(f"{icon} [{style}]{check.name}: {check.message}[/{style}]")

    console.print(f"\n[bold]Health score: {report.score}/100[/bold]")
