"""JSON-safe serialization helpers (no third-party dependencies).

Kept separate from ``utils.formatting`` so that modules which only need
JSON conversion (e.g. report generators) don't pull in a Rich console
dependency.
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any


def to_jsonable(obj: Any) -> Any:
    """Recursively convert dataclasses/sets/enums/etc. into JSON-safe structures."""
    if is_dataclass(obj) and not isinstance(obj, type):
        return {k: to_jsonable(v) for k, v in asdict(obj).items()}
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [to_jsonable(v) for v in obj]
    return obj


def print_json(obj: Any) -> None:
    """Print ``obj`` as clean JSON to stdout (no Rich markup)."""
    print(json.dumps(to_jsonable(obj), indent=2, default=str))
