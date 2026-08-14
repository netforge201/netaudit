"""CSV report generation for tabular data (e.g. scan results)."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def write_csv_report(rows: list[dict[str, Any]], output_path: Path) -> Path:
    """Write a list of flat dicts as a CSV report to ``output_path``."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        output_path.write_text("", encoding="utf-8")
        return output_path

    fieldnames = list(rows[0].keys())
    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return output_path
