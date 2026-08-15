"""Markdown report generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(lines)


def scan_to_markdown(scan_data: dict[str, Any]) -> str:
    """Render a scan-summary dict (as produced by 'netaudit scan --json') to Markdown."""
    lines = ["# NetAudit Network Scan Report", ""]
    hosts = scan_data.get("hosts", [])
    rows = []
    for host in hosts:
        rows.append(
            [
                host.get("ip", ""),
                host.get("status", "").upper(),
                f"{host.get('latency_ms')} ms" if host.get("latency_ms") is not None else "-",
                host.get("hostname") or "-",
            ]
        )
    lines.append(_table(["IP", "Status", "Latency", "Hostname"], rows))
    lines.append("")
    lines.append(f"**Discovered:** {scan_data.get('discovered', len(hosts))}  ")
    lines.append(f"**Online:** {scan_data.get('online', '-')}  ")
    lines.append(f"**Offline:** {scan_data.get('offline', '-')}  ")
    lines.append(f"**Duration:** {scan_data.get('duration_s', '-')}s")
    return "\n".join(lines)


def generic_to_markdown(title: str, data: Any) -> str:
    """Fallback renderer: pretty-print arbitrary JSON-like data as Markdown."""
    import json

    lines = [f"# {title}", "", "```json", json.dumps(data, indent=2, default=str), "```"]
    return "\n".join(lines)


def write_markdown_report(content: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path
