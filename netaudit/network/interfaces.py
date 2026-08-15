"""Local network interface enumeration using psutil."""

from __future__ import annotations

from dataclasses import dataclass, field

import psutil


@dataclass
class InterfaceInfo:
    name: str
    is_up: bool
    mtu: int | None
    mac: str | None
    ipv4: list[str] = field(default_factory=list)
    ipv6: list[str] = field(default_factory=list)
    bytes_sent: int | None = None
    bytes_recv: int | None = None
    packets_sent: int | None = None
    packets_recv: int | None = None
    errors_in: int | None = None
    errors_out: int | None = None
    drops_in: int | None = None
    drops_out: int | None = None


def list_interfaces() -> list[InterfaceInfo]:
    """Enumerate local network interfaces, their addresses and I/O counters."""
    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()
    io_counters = psutil.net_io_counters(pernic=True)

    interfaces: list[InterfaceInfo] = []
    for name, addr_list in addrs.items():
        stat = stats.get(name)
        io = io_counters.get(name)

        mac = None
        ipv4: list[str] = []
        ipv6: list[str] = []
        for addr in addr_list:
            family = str(addr.family)
            if "AF_LINK" in family or "AF_PACKET" in family:
                mac = addr.address or None
            elif addr.family.name == "AF_INET":
                ipv4.append(addr.address)
            elif addr.family.name == "AF_INET6":
                ipv6.append(addr.address.split("%")[0])

        interfaces.append(
            InterfaceInfo(
                name=name,
                is_up=bool(stat.isup) if stat else False,
                mtu=stat.mtu if stat else None,
                mac=mac,
                ipv4=ipv4,
                ipv6=ipv6,
                bytes_sent=io.bytes_sent if io else None,
                bytes_recv=io.bytes_recv if io else None,
                packets_sent=io.packets_sent if io else None,
                packets_recv=io.packets_recv if io else None,
                errors_in=io.errin if io else None,
                errors_out=io.errout if io else None,
                drops_in=io.dropin if io else None,
                drops_out=io.dropout if io else None,
            )
        )
    return sorted(interfaces, key=lambda i: i.name)
