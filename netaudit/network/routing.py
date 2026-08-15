"""Traceroute implementation using the system traceroute/tracert binary.

A pure-Python raw-socket traceroute would require root privileges on
most systems; shelling out to the platform's traceroute utility is
more portable and works with the same privilege model users already
have configured (e.g. setcap'd traceroute on Linux).
"""

from __future__ import annotations

import platform
import re
import shutil
import subprocess
from dataclasses import dataclass


class TracerouteUnavailableError(RuntimeError):
    """Raised when no traceroute-capable binary is available."""


@dataclass
class Hop:
    number: int
    address: str | None
    hostname: str | None
    rtt_ms: list[float]


@dataclass
class TracerouteResult:
    target: str
    hops: list[Hop]
    reached: bool
    error: str | None = None


def _find_binary() -> tuple[str, bool]:
    """Return (binary_path, is_windows_tracert)."""
    system = platform.system()
    if system == "Windows":
        binary = shutil.which("tracert")
        if binary:
            return binary, True
        raise TracerouteUnavailableError("'tracert' was not found on this system.")
    for name in ("traceroute",):
        binary = shutil.which(name)
        if binary:
            return binary, False
    raise TracerouteUnavailableError(
        "'traceroute' was not found. Install it (e.g. 'apt install "
        "traceroute' or 'brew install inetutils') to use this command."
    )


_HOP_LINE_RE = re.compile(r"^\s*(\d+)\s+(.*)$")
_RTT_RE = re.compile(r"([\d.]+)\s*ms")
_HOST_IP_RE = re.compile(r"([\w.\-]+)\s*\(([\d.:a-fA-F]+)\)")


def _parse_unix_output(output: str, max_hops: int) -> list[Hop]:
    hops: list[Hop] = []
    for line in output.splitlines():
        match = _HOP_LINE_RE.match(line)
        if not match:
            continue
        number = int(match.group(1))
        rest = match.group(2)
        if "* * *" in rest or rest.strip() == "*":
            hops.append(Hop(number=number, address=None, hostname=None, rtt_ms=[]))
            continue
        rtts = [float(x) for x in _RTT_RE.findall(rest)]
        host_ip = _HOST_IP_RE.search(rest)
        if host_ip:
            hostname, address = host_ip.group(1), host_ip.group(2)
        else:
            tokens = rest.split()
            address = tokens[0] if tokens else None
            hostname = None
        hops.append(Hop(number=number, address=address, hostname=hostname, rtt_ms=rtts))
    return hops


def traceroute(target: str, max_hops: int = 30, timeout: float = 2.0) -> TracerouteResult:
    """Run a traceroute to ``target`` and parse the hop-by-hop output."""
    try:
        binary, is_windows = _find_binary()
    except TracerouteUnavailableError as exc:
        return TracerouteResult(target, [], False, str(exc))

    if is_windows:
        cmd = [binary, "-h", str(max_hops), "-w", str(int(timeout * 1000)), target]
    else:
        cmd = [binary, "-m", str(max_hops), "-w", str(timeout), target]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout * max_hops + 10)
    except subprocess.TimeoutExpired:
        return TracerouteResult(target, [], False, "traceroute timed out")
    except OSError as exc:
        if "operation not permitted" in str(exc).lower():
            return TracerouteResult(
                target,
                [],
                False,
                "Permission denied. traceroute requires elevated privileges "
                "on this system (try running with sudo).",
            )
        return TracerouteResult(target, [], False, str(exc))

    output = proc.stdout + proc.stderr
    if "unknown host" in output.lower() or "cannot resolve" in output.lower():
        return TracerouteResult(target, [], False, f"Could not resolve host '{target}'")
    if "permission denied" in output.lower() or "operation not permitted" in output.lower():
        return TracerouteResult(
            target,
            [],
            False,
            "Permission denied while sending probe packets. Try running with sudo.",
        )

    hops = _parse_unix_output(output, max_hops)
    reached = bool(hops) and hops[-1].address == target or any(h.address == target for h in hops)
    return TracerouteResult(target=target, hops=hops, reached=reached, error=None)
