"""'netaudit report' - convert a saved JSON result into another report format."""
from __future__ import annotations

import json
from pathlib import Path

import typer

from netaudit.utils.formatting import console, err_console
from netaudit.utils.logging import get_logger

log = get_logger("commands.report")


def report(
    input_file: str = typer.Argument(..., help="Path to a JSON file produced with --json"),
    format: str = typer.Option("html", "--format", help="Output format: json, csv, markdown, html"),
    output: str = typer.Option(None, "--output", help="Output file path (default: reports/<name>.<ext>)"),
):
    """Convert INPUT_FILE (JSON) into the requested report FORMAT."""
    from netaudit.reports.csv import write_csv_report
    from netaudit.reports.html import generic_to_html, scan_to_html, write_html_report
    from netaudit.reports.json import write_json_report
    from netaudit.reports.markdown import (
        generic_to_markdown,
        scan_to_markdown,
        write_markdown_report,
    )

    in_path = Path(input_file)
    if not in_path.exists():
        err_console.print(f"[bold red]Error:[/bold red] File not found: {input_file}")
        raise typer.Exit(code=1) from None

    try:
        data = json.loads(in_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        err_console.print(f"[bold red]Error:[/bold red] Invalid JSON in {input_file}: {exc}")
        raise typer.Exit(code=1) from None

    is_scan = isinstance(data, dict) and "hosts" in data and "discovered" in data
    stem = in_path.stem

    format = format.lower()
    if format not in {"json", "csv", "markdown", "html"}:
        err_console.print(
            f"[bold red]Error:[/bold red] Unsupported format '{format}'. "
            "Choose from: json, csv, markdown, html"
        )
        raise typer.Exit(code=2) from None

    ext = {"json": "json", "csv": "csv", "markdown": "md", "html": "html"}[format]
    out_path = Path(output) if output else Path("reports") / f"{stem}.{ext}"

    if format == "json":
        write_json_report(data, out_path)
    elif format == "csv":
        if is_scan:
            rows = data["hosts"]
        elif isinstance(data, list):
            rows = data
        else:
            err_console.print(
                "[bold red]Error:[/bold red] CSV output requires list-shaped or "
                "scan-shaped JSON data."
            )
            raise typer.Exit(code=2) from None
        write_csv_report(rows, out_path)
    elif format == "markdown":
        content = scan_to_markdown(data) if is_scan else generic_to_markdown(stem, data)
        write_markdown_report(content, out_path)
    else:  # html
        content = scan_to_html(data) if is_scan else generic_to_html(stem, data)
        write_html_report(content, out_path)

    console.print(f"[bold green]Report written[/bold green]: {out_path}")
