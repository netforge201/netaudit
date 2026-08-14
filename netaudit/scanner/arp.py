"""ARP-based MAC address discovery and vendor lookup.

Requires raw socket access (root/CAP_NET_RAW on Linux, admin on
macOS/Windows). If Scapy or the required privileges are unavailable,
callers receive a clear error rather than a fake/empty result.
"""
from __future__ import annotations

from dataclasses import dataclass

try:
    from scapy.all import ARP, Ether, srp  # type: ignore

    SCAPY_AVAILABLE = True
except Exception:  # pragma: no cover - depends on optional/system deps
    SCAPY_AVAILABLE = False


class ArpUnavailableError(RuntimeError):
    """Raised when ARP scanning cannot be performed (missing scapy/perms)."""


@dataclass
class ArpEntry:
    ip: str
    mac: str


def arp_scan(network_cidr: str, timeout: float = 2.0) -> list[ArpEntry]:
    """Send ARP who-has requests across ``network_cidr`` and collect replies.

    Only works for IPv4 networks on a locally-attached broadcast domain
    (i.e. not across routed subnets). Requires root/administrator
    privileges because it uses raw sockets.
    """
    if not SCAPY_AVAILABLE:
        raise ArpUnavailableError(
            "Scapy is not available or failed to import. Install scapy "
            "and required system packet-capture libraries (e.g. libpcap) "
            "to enable ARP/MAC discovery."
        )

    try:
        request = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=network_cidr)
        answered, _ = srp(request, timeout=timeout, verbose=False)
    except PermissionError as exc:
        raise ArpUnavailableError(
            "Permission denied sending raw ARP packets. Re-run with root "
            "privileges (e.g. sudo) to enable MAC address discovery."
        ) from exc
    except OSError as exc:
        raise ArpUnavailableError(f"ARP scan failed: {exc}") from exc

    entries = []
    for _, received in answered:
        entries.append(ArpEntry(ip=received.psrc, mac=received.hwsrc))
    return entries


def lookup_mac(ip: str, timeout: float = 2.0) -> str | None:
    """Return the MAC address for a single ``ip`` via ARP, or None if no reply."""
    if not SCAPY_AVAILABLE:
        return None
    try:
        request = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip)
        answered, _ = srp(request, timeout=timeout, verbose=False)
    except (PermissionError, OSError):
        return None
    for _, received in answered:
        return received.hwsrc
    return None
