"""'netaudit config' - show and initialize NetAudit configuration."""
from __future__ import annotations

import typer
import yaml

from netaudit.config.settings import CONFIG_FILE, init_config, load_settings
from netaudit.utils.formatting import console, err_console, print_json

app = typer.Typer(help="Show or initialize NetAudit configuration.")


@app.command("show")
def show(json_output: bool = typer.Option(False, "--json", help="Output as JSON")):
    """Show the currently active (merged) configuration."""
    settings = load_settings()
    data = settings.model_dump()

    if json_output:
        print_json(data)
        return

    console.print(f"\n[bold]NetAudit Configuration[/bold] ({CONFIG_FILE})")
    console.rule(style="dim")
    console.print(yaml.dump(data, sort_keys=False, default_flow_style=False))


@app.command("init")
def init(force: bool = typer.Option(False, "--force", help="Overwrite existing config")):
    """Write a default config.yaml to ~/.netaudit/config.yaml."""
    try:
        path = init_config(force=force)
    except FileExistsError as exc:
        err_console.print(f"[bold red]Error:[/bold red] {exc}. Use --force to overwrite.")
        raise typer.Exit(code=1) from None
    console.print(f"[bold green]Config written[/bold green]: {path}")
