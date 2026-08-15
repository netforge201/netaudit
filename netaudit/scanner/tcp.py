"""TCP connect-scan implementation.

Uses plain ``socket.connect`` (a "connect scan") rather than raw SYN
packets, so it works without elevated privileges. This is slower than
a SYN scan but portable and dependency-free.
"""

from __future__ import annotations

import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass


@dataclass
class PortResult:
    port: int
    state: str  # "open", "closed", "filtered"
    service: str


def check_port(host: str, port: int, timeout: float = 1.0) -> PortResult:
    """Attempt a TCP connect to ``host:port`` and report open/closed/filtered."""
    from netaudit.utils.services import service_name

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            state = "open" if result == 0 else "closed"
    except TimeoutError:
        state = "filtered"
    except (socket.gaierror, OSError):
        state = "filtered"

    return PortResult(port=port, state=state, service=service_name(port))


def scan_ports(
    host: str, ports: list[int], timeout: float = 1.0, workers: int = 50
) -> list[PortResult]:
    """Scan ``ports`` on ``host`` concurrently and return results in port order."""
    results: dict[int, PortResult] = {}
    with ThreadPoolExecutor(max_workers=max(1, min(workers, len(ports) or 1))) as pool:
        futures = {pool.submit(check_port, host, p, timeout): p for p in ports}
        for future in as_completed(futures):
            res = future.result()
            results[res.port] = res
    return [results[p] for p in ports]
