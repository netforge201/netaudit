"""Shared Rich console instances for command output.

Pure-data helpers (service name lookups, JSON serialization) live in
``utils.services`` and ``utils.serialization`` respectively, kept free
of the Rich dependency, and re-exported here for convenience.
"""

from __future__ import annotations

from rich.console import Console

from netaudit.utils.serialization import print_json, to_jsonable
from netaudit.utils.services import COMMON_TCP_PORTS, SERVICE_NAMES, service_name

__all__ = [
    "console",
    "err_console",
    "COMMON_TCP_PORTS",
    "SERVICE_NAMES",
    "service_name",
    "to_jsonable",
    "print_json",
]

# stdout console: this is where actual command RESULTS go.
console = Console()
# stderr console: used for warnings/errors that shouldn't pollute
# stdout when the user is piping JSON/CSV output into another tool.
err_console = Console(stderr=True)
