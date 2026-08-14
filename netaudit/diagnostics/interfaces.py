"""Interface status/error parsing for device-based diagnostics.

Parsing focuses on Cisco IOS/IOS-XE output (the most common lab/prod
target for Netmiko-based tooling). For other platforms, if the output
doesn't match expected patterns, checks are marked as skipped rather
than guessed at.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class InterfaceStatus:
    name: str
    status: str
    protocol: str


@dataclass
class InterfaceErrorStats:
    name: str
    input_errors: int
    output_errors: int
    crc_errors: int


_BRIEF_LINE_RE = re.compile(
    r"^(?P<name>\S+)\s+\S+\s+\S+\s+\S+\s+"
    r"(?P<status>up|down|administratively down)\s+(?P<protocol>up|down)\s*$",
    re.IGNORECASE,
)
# Note: exactly 3 placeholder columns (IP-Address, OK?, Method) between
# the interface name and Status, matching Cisco's 6-column brief output.


def parse_ios_interfaces_brief(raw: str) -> list[InterfaceStatus]:
    """Parse Cisco 'show ip interface brief' output."""
    results: list[InterfaceStatus] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.lower().startswith("interface"):
            continue
        match = _BRIEF_LINE_RE.match(line)
        if match:
            results.append(InterfaceStatus(
                name=match.group("name"),
                status=match.group("status").lower(),
                protocol=match.group("protocol").lower(),
            ))
    return results


_IFACE_BLOCK_RE = re.compile(r"^(\S+) is (.+?), line protocol is (\w+)", re.MULTILINE)
_ERROR_LINE_RE = re.compile(
    r"(\d+)\s+input errors.*?(\d+)\s+CRC", re.IGNORECASE
)
_OUTPUT_ERROR_RE = re.compile(r"(\d+)\s+output errors", re.IGNORECASE)


def parse_ios_interface_errors(raw: str) -> list[InterfaceErrorStats]:
    """Parse Cisco 'show interfaces' output for input/output/CRC error counters."""
    results: list[InterfaceErrorStats] = []
    blocks = re.split(r"\n(?=\S+ is )", raw)
    for block in blocks:
        header = re.match(r"^(\S+) is", block)
        if not header:
            continue
        name = header.group(1)
        in_err_match = _ERROR_LINE_RE.search(block)
        out_err_match = _OUTPUT_ERROR_RE.search(block)
        input_errors = int(in_err_match.group(1)) if in_err_match else 0
        crc_errors = int(in_err_match.group(2)) if in_err_match else 0
        output_errors = int(out_err_match.group(1)) if out_err_match else 0
        results.append(InterfaceErrorStats(
            name=name,
            input_errors=input_errors,
            output_errors=output_errors,
            crc_errors=crc_errors,
        ))
    return results
