"""Tests for netaudit.reports (JSON/CSV/Markdown/HTML generation)."""
from __future__ import annotations

import json
from pathlib import Path

from netaudit.reports.csv import write_csv_report
from netaudit.reports.html import generic_to_html, scan_to_html, write_html_report
from netaudit.reports.json import write_json_report
from netaudit.reports.markdown import (
    generic_to_markdown,
    scan_to_markdown,
    write_markdown_report,
)

SAMPLE_SCAN = {
    "target": "192.168.1.0/30",
    "hosts": [
        {"ip": "192.168.1.1", "status": "up", "latency_ms": 1.2,
         "hostname": "router.local", "mac": None, "vendor": None},
        {"ip": "192.168.1.2", "status": "down", "latency_ms": None,
         "hostname": None, "mac": None, "vendor": None},
    ],
    "discovered": 2, "online": 1, "offline": 1, "duration_s": 0.5,
}


def test_write_json_report(tmp_path: Path):
    out = write_json_report(SAMPLE_SCAN, tmp_path / "scan.json")
    data = json.loads(out.read_text())
    assert data["discovered"] == 2
    assert len(data["hosts"]) == 2


def test_write_csv_report(tmp_path: Path):
    out = write_csv_report(SAMPLE_SCAN["hosts"], tmp_path / "scan.csv")
    content = out.read_text()
    assert "192.168.1.1" in content
    assert content.startswith("ip,status")


def test_write_csv_report_empty_rows(tmp_path: Path):
    out = write_csv_report([], tmp_path / "empty.csv")
    assert out.read_text() == ""


def test_scan_to_markdown_contains_hosts():
    md = scan_to_markdown(SAMPLE_SCAN)
    assert "192.168.1.1" in md
    assert "Discovered" in md


def test_generic_to_markdown_embeds_json():
    md = generic_to_markdown("Custom Report", {"a": 1})
    assert "Custom Report" in md
    assert '"a": 1' in md


def test_write_markdown_report(tmp_path: Path):
    out = write_markdown_report("# Hello", tmp_path / "r.md")
    assert out.read_text() == "# Hello"


def test_scan_to_html_contains_hosts():
    html = scan_to_html(SAMPLE_SCAN)
    assert "192.168.1.1" in html
    assert "<table>" in html


def test_generic_to_html_escapes_content():
    html = generic_to_html("Report", {"note": "<script>alert(1)</script>"})
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_write_html_report(tmp_path: Path):
    out = write_html_report("<p>hi</p>", tmp_path / "r.html")
    assert out.read_text() == "<p>hi</p>"
