"""JSON report generation."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from netaudit.utils.serialization import to_jsonable


def write_json_report(data: Any, output_path: Path) -> Path:
    """Write ``data`` as a formatted JSON report to ``output_path``."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(to_jsonable(data), fh, indent=2, default=str)
    return output_path
