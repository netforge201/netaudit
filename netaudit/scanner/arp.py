"""ARP-based MAC address discovery.

Uses the system ARP/neighbor table as the preferred method and Scapy
as an optional fallback. This allows MAC discovery on macOS without
requiring direct access to /dev/bpf* in the common case.
"""

from __future__ import annotations

import platform
import re
import shutil
import subprocess
from dataclasses import dataclass

try:
    from scapy.all import ARP, Ether, srp  # type: ignore

    SCAPY_AVAILABLE = True
except Exception:  # pragma: no cover
    SCAPY_AVAILABLE = False


class ArpUnavailableError(RuntimeError):
    """Raised when ARP scanning cannot be performed."""


@dataclass
class ArpEntry:
    ip: str
    mac: str


def _normalize_mac(mac: str) -> str | None:
    """Normalize a MAC address, accepting one- or two-digit octets."""
    parts = mac.strip().lower().replace("-", ":").split(":")
    if len(parts) != 6:
        return None

    try:
        normalized = ":".join(f"{int(part, 16):02x}" for part in parts)
    except ValueError:
        return None

    return normalized


def _system_lookup_mac(ip: str) -> str | None:
    """Look up an IP in the operating system ARP/neighbor table."""
    system = platform.system()

    try:
        if system == "Darwin":
            arp = shutil.which("arp")
            if not arp:
                return None

            proc = subprocess.run(
                [arp, "-an"],
                capture_output=True,
                text=True,
                timeout=2,
            )

            pattern = re.compile(
                rf"\({re.escape(ip)}\)\s+at\s+"
                r"([0-9a-fA-F]{1,2}(?::[0-9a-fA-F]{1,2}){5})\b"
            )

            match = pattern.search(proc.stdout)
            return _normalize_mac(match.group(1)) if match else None

        if system == "Linux":
            ip_cmd = shutil.which("ip")

            if ip_cmd:
                proc = subprocess.run(
                    [ip_cmd, "neigh", "show"],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )

                for line in proc.stdout.splitlines():
                    if not line.startswith(ip + " "):
                        continue

                    match = re.search(
                        r"\blladdr\s+"
                        r"([0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5})\\b",
                        line,
                    )

                    if match:
                        return _normalize_mac(match.group(1))

            arp = shutil.which("arp")

            if arp:
                proc = subprocess.run(
                    [arp, "-an"],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )

                for line in proc.stdout.splitlines():
                    if ip not in line:
                        continue

                    match = re.search(
                        r"\b([0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5})\b",
                        line,
                    )

                    if match:
                        return _normalize_mac(match.group(1))

    except (OSError, subprocess.SubprocessError):
        return None

    return None


def _scapy_lookup_mac(ip: str, timeout: float) -> str | None:
    if not SCAPY_AVAILABLE:
        return None

    try:
        request = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip)
        answered, _ = srp(request, timeout=timeout, verbose=False)
    except Exception:
        return None

    for _, received in answered:
        return _normalize_mac(received.hwsrc)

    return None


def arp_scan(network_cidr: str, timeout: float = 2.0) -> list[ArpEntry]:
    """Discover MAC addresses on a locally attached IPv4 network."""
    entries: dict[str, ArpEntry] = {}

    # Populate the system neighbor table first by checking each address.
    # The actual ICMP discovery in NetAudit will normally have already
    # populated entries for reachable hosts.
    try:
        import ipaddress

        network = ipaddress.ip_network(network_cidr, strict=False)
        for ip in network.hosts():
            ip_str = str(ip)
            mac = _system_lookup_mac(ip_str)
            if mac:
                entries[ip_str] = ArpEntry(ip=ip_str, mac=mac)
    except (ValueError, OSError):
        pass

    if entries:
        return list(entries.values())

    if not SCAPY_AVAILABLE:
        raise ArpUnavailableError(
            "No MAC addresses were found in the system ARP table and Scapy is unavailable."
        )

    # Scapy fallback. Permission errors simply result in an empty list.
    try:
        request = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=network_cidr)
        answered, _ = srp(request, timeout=timeout, verbose=False)
    except Exception:
        return []

    for _, received in answered:
        mac = _normalize_mac(received.hwsrc)
        if mac:
            entries[received.psrc] = ArpEntry(
                ip=received.psrc,
                mac=mac,
            )

    return list(entries.values())


def lookup_mac(ip: str, timeout: float = 2.0) -> str | None:
    """Return a MAC address using the system ARP table, then Scapy."""
    mac = _system_lookup_mac(ip)
    if mac:
        return mac

    return _scapy_lookup_mac(ip, timeout)
