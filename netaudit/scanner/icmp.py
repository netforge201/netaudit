"""ICMP-based reachability checks.

Uses the system ``ping`` binary rather than raw sockets so that the
tool works without root privileges or elevated capabilities on most
platforms (Linux ping binaries are typically setuid/setcap already).
"""
from __future__ import annotations

import platform
import re
import shutil
import subprocess
from dataclasses import dataclass


class PingUnavailableError(RuntimeError):
    """Raised when the system ``ping`` utility cannot be found."""


@dataclass
class PingResult:
    target: str
    reachable: bool
    packets_sent: int
    packets_received: int
    packet_loss_pct: float
    min_ms: float | None
    avg_ms: float | None
    max_ms: float | None
    raw_times_ms: list[float]
    error: str | None = None
    ttl: int | None = None


def _ping_binary() -> str:
    binary = shutil.which("ping")
    if not binary:
        raise PingUnavailableError(
            "The 'ping' system utility was not found on this machine."
        )
    return binary


def _build_command(target: str, count: int, timeout: float, interval: float) -> list[str]:
    binary = _ping_binary()
    system = platform.system()
    if system == "Darwin":
        return [binary, "-c", str(count), "-W", str(int(timeout * 1000)),
                "-i", str(max(interval, 0.2)), target]
    if system == "Windows":
        return [binary, "-n", str(count), "-w", str(int(timeout * 1000)), target]
    # Linux / other POSIX
    return [binary, "-c", str(count), "-W", str(max(int(timeout), 1)),
            "-i", str(max(interval, 0.2)), target]


_TIME_RE = re.compile(r"time[=<]([\d.]+)\s*ms", re.IGNORECASE)
_TTL_RE = re.compile(r"ttl[=](\d+)", re.IGNORECASE)
_LOSS_RE = re.compile(r"([\d.]+)%\s*(?:packet)?\s*loss", re.IGNORECASE)
_STATS_RE = re.compile(
    r"(?:min/avg/max(?:/mdev)?|Minimum|Maximum|Average)\s*=?\s*"
    r"([\d.]+)[/\s]*ms?\s*,?\s*([\d.]+)?[/\s]*ms?\s*,?\s*([\d.]+)?",
    re.IGNORECASE,
)


def ping(target: str, count: int = 4, timeout: float = 2.0, interval: float = 1.0) -> PingResult:
    """Ping ``target`` using the system ping utility and parse the results."""
    try:
        cmd = _build_command(target, count, timeout, interval)
    except PingUnavailableError as exc:
        return PingResult(target, False, count, 0, 100.0, None, None, None, [], str(exc))

    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout * count + 5
        )
    except subprocess.TimeoutExpired:
        return PingResult(target, False, count, 0, 100.0, None, None, None, [],
                           "ping command timed out")
    except OSError as exc:
        return PingResult(target, False, count, 0, 100.0, None, None, None, [], str(exc))

    output = proc.stdout + proc.stderr
    times = [float(m) for m in _TIME_RE.findall(output)]
    received = len(times)
    ttl_matches = _TTL_RE.findall(output)
    ttl = int(ttl_matches[0]) if ttl_matches else None

    loss_match = _LOSS_RE.search(output)
    loss_pct = float(loss_match.group(1)) if loss_match else (
        100.0 if received == 0 else round(100 * (1 - received / count), 1)
    )

    reachable = received > 0
    error = None
    if not reachable:
        if "unknown host" in output.lower() or "cannot resolve" in output.lower():
            error = f"Could not resolve host '{target}'"
        elif "network is unreachable" in output.lower():
            error = "Network is unreachable"
        elif "permission denied" in output.lower() or "operation not permitted" in output.lower():
            error = "Permission denied while sending ICMP packets"
        else:
            error = "Host did not respond to ICMP echo requests"

    return PingResult(
        target=target,
        reachable=reachable,
        packets_sent=count,
        packets_received=received,
        packet_loss_pct=loss_pct,
        min_ms=min(times) if times else None,
        avg_ms=round(sum(times) / len(times), 2) if times else None,
        max_ms=max(times) if times else None,
        raw_times_ms=times,
        error=error,
        ttl=ttl,
    )


def quick_probe(target: str, timeout: float = 1.0) -> PingResult:
    """A fast single-packet reachability probe, used by the network scanner."""
    return ping(target, count=1, timeout=timeout, interval=0.2)


def os_hint_from_ttl(ttl: int | None) -> str | None:
    """Return a best-effort, non-authoritative OS family hint from an observed TTL.

    This is a heuristic only (based on common default initial TTL values)
    and can be wrong due to hop count or TTL modification - never
    presented as a definitive OS fingerprint.
    """
    if ttl is None:
        return None
    if ttl <= 64:
        return "Likely Linux/Unix/macOS (TTL<=64)"
    if ttl <= 128:
        return "Likely Windows (TTL<=128)"
    if ttl <= 255:
        return "Likely network device/router (TTL<=255)"
    return None
