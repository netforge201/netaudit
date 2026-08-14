"""Device-side service/protocol parsers used by 'netaudit doctor' when a
live device connection is available (CPU, memory, uptime, routing,
ARP, NTP, BGP, OSPF). Cisco IOS-oriented; unmatched output is
reported as unavailable rather than guessed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class DeviceHealth:
    uptime: str | None = None
    cpu_pct: float | None = None
    memory_used_pct: float | None = None


_UPTIME_RE = re.compile(r"uptime is (.+)", re.IGNORECASE)
_CPU_RE = re.compile(r"CPU utilization for five seconds:\s*(\d+)%", re.IGNORECASE)
_MEM_RE = re.compile(
    r"Processor Pool Total:\s*(\d+)\s+Used:\s*(\d+)\s+Free:\s*(\d+)", re.IGNORECASE
)


def parse_ios_version(raw: str) -> DeviceHealth:
    """Parse Cisco IOS 'show version' for uptime (CPU/memory need separate cmds)."""
    health = DeviceHealth()
    uptime_match = _UPTIME_RE.search(raw)
    if uptime_match:
        health.uptime = uptime_match.group(1).strip()
    return health


def parse_ios_cpu(raw: str) -> float | None:
    match = _CPU_RE.search(raw)
    return float(match.group(1)) if match else None


def parse_ios_memory(raw: str) -> float | None:
    match = _MEM_RE.search(raw)
    if not match:
        return None
    total, used, _free = (int(x) for x in match.groups())
    if total == 0:
        return None
    return round(100 * used / total, 1)


_DEFAULT_ROUTE_RE = re.compile(r"^S\*?\s+0\.0\.0\.0/0", re.MULTILINE)
_GATEWAY_ROUTE_RE = re.compile(r"^Gateway of last resort is (\S+)", re.MULTILINE)


def has_default_route(raw: str) -> bool:
    """Check Cisco 'show ip route' output for a default route entry."""
    if _GATEWAY_ROUTE_RE.search(raw) and "not set" not in raw:
        return True
    return bool(_DEFAULT_ROUTE_RE.search(raw))


def parse_ntp_status(raw: str) -> bool | None:
    """Return True if NTP is synchronized, False if not, None if command unsupported."""
    lowered = raw.lower()
    if "% invalid" in lowered or "% unknown" in lowered or "% ambiguous" in lowered:
        return None
    if "clock is synchronized" in lowered:
        return True
    if "clock is unsynchronized" in lowered:
        return False
    return None


def parse_bgp_summary(raw: str) -> tuple[int, int] | None:
    """Return (total_neighbors, established_neighbors) from 'show ip bgp summary'."""
    lowered = raw.lower()
    if "% invalid" in lowered or "% unknown" in lowered or "bgp not active" in lowered:
        return None
    lines = raw.splitlines()
    neighbor_lines = [
        l for l in lines
        if re.match(r"^\d+\.\d+\.\d+\.\d+\s", l.strip())
    ]
    if not neighbor_lines:
        return None
    established = sum(1 for l in neighbor_lines if not re.search(r"\bIdle\b|\bActive\b|\bConnect\b", l))
    return len(neighbor_lines), established


def parse_ospf_neighbors(raw: str) -> tuple[int, int] | None:
    """Return (total_neighbors, full_neighbors) from 'show ip ospf neighbor'."""
    lowered = raw.lower()
    if "% invalid" in lowered or "% unknown" in lowered or "ospf process" not in lowered and "neighbor id" not in lowered:
        return None
    lines = [l for l in raw.splitlines() if re.match(r"^\d+\.\d+\.\d+\.\d+\s", l.strip())]
    if not lines:
        return None
    full = sum(1 for l in lines if "full" in l.lower())
    return len(lines), full
