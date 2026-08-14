"""NetAudit CLI entrypoint - wires together all subcommands.

Design note on command registration: single-action commands that take
a positional TARGET argument plus options (scan, host, ports, ping,
dns, route, interfaces, doctor, report, snapshot) are registered
directly on the top-level Typer app via `app.command(...)`, NOT as
nested Typer sub-apps with a callback. Click's argument parser treats
any group (which is what a callback-based sub-app becomes) as ending
its own option-parsing once it consumes the first positional
argument - so e.g. `netaudit scan 10.0.0.0/24 --ports 22,80` would
fail to recognize `--ports` if `scan` were implemented as a nested
group. This was verified directly against Click 8.3 during
development. Commands that have genuine subcommands with no
competing default argument (device, config) remain nested Typer
sub-apps, since that pattern is unaffected by the issue.
"""
from __future__ import annotations

import sys

import typer
from rich.panel import Panel
from rich.text import Text

from netaudit import __version__
from netaudit.utils.formatting import console, err_console
from netaudit.utils.logging import setup_logging
from netaudit.utils.validators import ValidationError

app = typer.Typer(
    name="netaudit",
    help="NetAudit - Network Audit & Diagnostics Toolkit for network engineers.",
    add_completion=True,
    no_args_is_help=False,
    rich_markup_mode="rich",
)


def _register_commands() -> None:
    from netaudit.commands import config as config_cmd
    from netaudit.commands import device as device_cmd
    from netaudit.commands.diff import diff
    from netaudit.commands.dns import dns
    from netaudit.commands.doctor import doctor
    from netaudit.commands.host import host
    from netaudit.commands.interfaces import interfaces
    from netaudit.commands.ping import ping
    from netaudit.commands.ports import ports
    from netaudit.commands.report import report
    from netaudit.commands.route import route
    from netaudit.commands.scan import scan
    from netaudit.commands.snapshot import snapshot

    # Single-action leaf commands - registered directly (see module docstring above).
    app.command("scan", help="Discover live hosts on a network.")(scan)
    app.command("host", help="Show detailed information about a single host.")(host)
    app.command("ports", help="Scan TCP ports on a host.")(ports)
    app.command("ping", help="Ping a host and report latency/loss statistics.")(ping)
    app.command("dns", help="Look up DNS records for a domain or IP.")(dns)
    app.command("route", help="Trace the network route to a host.")(route)
    app.command("interfaces", help="List local network interfaces.")(interfaces)
    app.command("doctor", help="Run a comprehensive network health check.")(doctor)
    app.command("report", help="Convert a JSON result into CSV, Markdown, or HTML.")(report)
    app.command("snapshot", help="Capture and list device state snapshots.")(snapshot)
    app.command("diff", help="Compare the two most recent snapshots of a device.")(diff)

    # Genuine multi-subcommand groups.
    app.add_typer(device_cmd.app, name="device", help="Connect to and query network devices.")
    app.add_typer(config_cmd.app, name="config", help="Show or initialize configuration.")


_register_commands()


def _print_banner() -> None:
    banner = Text()
    banner.append("NetAudit", style="bold cyan")
    banner.append(f"  v{__version__}\n", style="dim")
    banner.append("Network Audit & Diagnostics Toolkit", style="italic")
    console.print(Panel(banner, expand=False, border_style="cyan"))
    console.print(
        "\n[bold]Usage:[/bold] netaudit [cyan]COMMAND[/cyan] [dim][OPTIONS][/dim]\n"
    )
    console.print("[bold]Commands:[/bold]")
    commands = [
        ("scan", "Discover live hosts on a network"),
        ("host", "Show detailed info about a single host"),
        ("ports", "Scan TCP ports on a host"),
        ("ping", "Ping a host and report statistics"),
        ("dns", "Look up DNS records"),
        ("route", "Trace the network route to a host"),
        ("interfaces", "List local network interfaces"),
        ("device", "Connect to / query network devices"),
        ("snapshot", "Capture or list device state snapshots"),
        ("diff", "Compare two device snapshots"),
        ("doctor", "Run a comprehensive health check"),
        ("report", "Convert results into CSV/Markdown/HTML"),
        ("config", "Show or initialize configuration"),
        ("version", "Show the NetAudit version"),
    ]
    for name, desc in commands:
        console.print(f"  [cyan]{name:<12}[/cyan] {desc}")
    console.print("\nRun [cyan]netaudit COMMAND --help[/cyan] for details on any command.\n")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", help="Enable INFO-level logging"),
    debug: bool = typer.Option(False, "--debug", help="Enable DEBUG-level logging and tracebacks"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable colored output"),
    version: bool = typer.Option(False, "--version", help="Show version and exit"),
):
    """NetAudit - Network Audit & Diagnostics Toolkit."""
    setup_logging(verbose=verbose, debug=debug)
    ctx.obj = {"debug": debug}

    if no_color:
        console.no_color = True
        err_console.no_color = True

    if version:
        console.print(f"netaudit {__version__}")
        raise typer.Exit(code=0)

    if ctx.invoked_subcommand is None:
        _print_banner()
        raise typer.Exit(code=0)


@app.command("version", help="Show the NetAudit version.")
def version_cmd() -> None:
    """Show the NetAudit version."""
    console.print(f"netaudit {__version__}")


def run() -> None:
    """Console-script entrypoint with top-level error handling."""
    debug_mode = "--debug" in sys.argv

    try:
        app()
    except ValidationError as exc:
        err_console.print(f"[bold red]Error:[/bold red] {exc}")
        sys.exit(2)
    except KeyboardInterrupt:
        err_console.print("\n[yellow]Interrupted.[/yellow]")
        sys.exit(130)
    except Exception as exc:  # noqa: BLE001 - top-level safety net
        if debug_mode:
            raise
        err_console.print(f"[bold red]Unexpected error:[/bold red] {exc}")
        err_console.print("[dim]Run with --debug for a full traceback.[/dim]")
        sys.exit(1)


if __name__ == "__main__":
    run()
