"""Input validation helpers shared across NetAudit commands."""
from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass

# Reject scans larger than this many hosts to avoid accidental
# denial-of-service against a network (e.g. netaudit scan 0.0.0.0/0).
MAX_SCAN_HOSTS = 65536

_HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)"
    r"(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*\.?$"
)


class ValidationError(ValueError):
    """Raised when user-supplied input fails validation."""


@dataclass
class PortRange:
    """A resolved, deduplicated, sorted list of TCP/UDP ports."""

    ports: list[int]

    def __iter__(self):
        return iter(self.ports)

    def __len__(self) -> int:
        return len(self.ports)


def validate_ip(value: str) -> str:
    """Validate that ``value`` is a syntactically valid IPv4/IPv6 address."""
    try:
        ipaddress.ip_address(value)
    except ValueError as exc:
        raise ValidationError(f"'{value}' is not a valid IP address") from exc
    return value


def validate_target(value: str) -> str:
    """Validate that ``value`` is either a valid IP address or hostname."""
    try:
        ipaddress.ip_address(value)
        return value
    except ValueError:
        pass
    if _HOSTNAME_RE.match(value):
        return value
    raise ValidationError(f"'{value}' is not a valid IP address or hostname")


def parse_cidr(value: str) -> ipaddress.IPv4Network | ipaddress.IPv6Network:
    """Parse and validate a CIDR network, enforcing a sane host-count limit.

    A bare IP address (no ``/prefix``) is treated as a ``/32`` (or ``/128``
    for IPv6) single-host network so ``netaudit scan 192.168.1.1`` works too.
    """
    try:
        network = ipaddress.ip_network(value, strict=False)
    except ValueError as exc:
        raise ValidationError(f"'{value}' is not a valid CIDR network") from exc

    host_count = network.num_addresses
    if host_count > MAX_SCAN_HOSTS:
        raise ValidationError(
            f"Network '{value}' contains {host_count:,} addresses, which "
            f"exceeds the safety limit of {MAX_SCAN_HOSTS:,}. "
            "Use a smaller CIDR range (e.g. a /24 or smaller)."
        )
    return network


def parse_ports(spec: str) -> PortRange:
    """Parse a port specification like ``'22,80,443'`` or ``'1-1024'``.

    Comma-separated values and ranges can be mixed, e.g. ``'22,80,1000-1010'``.
    """
    ports: set[int] = set()
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            start_s, _, end_s = chunk.partition("-")
            try:
                start, end = int(start_s), int(end_s)
            except ValueError as exc:
                raise ValidationError(f"Invalid port range '{chunk}'") from exc
            if not (0 < start <= 65535 and 0 < end <= 65535 and start <= end):
                raise ValidationError(f"Invalid port range '{chunk}'")
            ports.update(range(start, end + 1))
        else:
            try:
                port = int(chunk)
            except ValueError as exc:
                raise ValidationError(f"Invalid port '{chunk}'") from exc
            if not 0 < port <= 65535:
                raise ValidationError(f"Port '{chunk}' out of range (1-65535)")
            ports.add(port)

    if not ports:
        raise ValidationError("No ports specified")
    return PortRange(sorted(ports))
