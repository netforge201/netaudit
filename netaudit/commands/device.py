"""'netaudit device' - connect to and query network devices via Netmiko."""
from __future__ import annotations

import typer

from netaudit.utils.formatting import console, err_console, print_json
from netaudit.utils.logging import get_logger
from netaudit.utils.validators import ValidationError, validate_target

app = typer.Typer(help="Connect to and query network devices.")
log = get_logger("commands.device")


@app.command("connect")
def connect(
    target: str = typer.Argument(..., help="Device IP address or hostname"),
    username: str | None = typer.Option(None, "--username", envvar="NETAUDIT_USERNAME"),
    password: str | None = typer.Option(
        None, "--password", envvar="NETAUDIT_PASSWORD",
        help="Discouraged on the command line; prefer env vars or the interactive prompt."
    ),
    device_type: str = typer.Option("cisco_ios", "--device-type", help="Netmiko device_type"),
    port: int = typer.Option(22, "--port", help="SSH port"),
):
    """Test connectivity/authentication to a device (no commands are run)."""
    from netaudit.devices.connector import (
        DeviceAuthenticationError,
        DeviceConnectionError,
        MissingDependencyError,
        device_session,
        resolve_credentials,
    )

    try:
        validate_target(target)
    except ValidationError as exc:
        err_console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=2)

    try:
        creds = resolve_credentials(username, password)
        with device_session(target, device_type, creds, port=port):
            pass
    except MissingDependencyError as exc:
        err_console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1)
    except DeviceAuthenticationError as exc:
        err_console.print(f"[bold red]Authentication failed:[/bold red] {exc}")
        raise typer.Exit(code=4)
    except DeviceConnectionError as exc:
        err_console.print(f"[bold red]Connection failed:[/bold red] {exc}")
        raise typer.Exit(code=3)

    console.print(f"[bold green]Connected successfully[/bold green] to {target} "
                  f"({device_type}).")


@app.command("info")
def info(
    target: str = typer.Argument(..., help="Device IP address or hostname"),
    username: str | None = typer.Option(None, "--username", envvar="NETAUDIT_USERNAME"),
    password: str | None = typer.Option(None, "--password", envvar="NETAUDIT_PASSWORD"),
    device_type: str = typer.Option("cisco_ios", "--device-type", help="Netmiko device_type"),
    port: int = typer.Option(22, "--port", help="SSH port"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Connect to a device and retrieve read-only status information."""
    from netaudit.devices import module_for
    from netaudit.devices.connector import (
        DeviceAuthenticationError,
        DeviceConnectionError,
        MissingDependencyError,
        device_session,
        resolve_credentials,
    )

    try:
        validate_target(target)
    except ValidationError as exc:
        err_console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=2)

    try:
        creds = resolve_credentials(username, password)
        with device_session(target, device_type, creds, port=port) as conn:
            module = module_for(device_type)
            output = module.collect_info(conn)
    except MissingDependencyError as exc:
        err_console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1)
    except DeviceAuthenticationError as exc:
        err_console.print(f"[bold red]Authentication failed:[/bold red] {exc}")
        raise typer.Exit(code=4)
    except DeviceConnectionError as exc:
        err_console.print(f"[bold red]Connection failed:[/bold red] {exc}")
        raise typer.Exit(code=3)

    if json_output:
        print_json({"target": target, "device_type": device_type, "sections": output})
        return

    console.print(f"\n[bold]Device info: {target} ({device_type})[/bold]")
    for label, content in output.items():
        console.rule(f"[cyan]{label}[/cyan]", style="dim")
        console.print(content)
