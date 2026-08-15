"""DNS lookup helpers built on dnspython."""

from __future__ import annotations

from dataclasses import dataclass, field

import dns.exception
import dns.resolver
import dns.reversename


class DnsLookupError(RuntimeError):
    """Raised when a DNS query fails in a way the caller should handle."""


@dataclass
class DnsRecords:
    name: str
    a: list[str] = field(default_factory=list)
    aaaa: list[str] = field(default_factory=list)
    mx: list[str] = field(default_factory=list)
    ns: list[str] = field(default_factory=list)
    txt: list[str] = field(default_factory=list)
    cname: list[str] = field(default_factory=list)
    errors: dict[str, str] = field(default_factory=dict)


_RECORD_TYPES = ["A", "AAAA", "MX", "NS", "TXT", "CNAME"]


def lookup(name: str, timeout: float = 3.0) -> DnsRecords:
    """Query common DNS record types for ``name``."""
    resolver = dns.resolver.Resolver()
    resolver.timeout = timeout
    resolver.lifetime = timeout

    records = DnsRecords(name=name)
    for rtype in _RECORD_TYPES:
        try:
            answer = resolver.resolve(name, rtype)
            values = []
            for rdata in answer:
                if rtype == "MX":
                    values.append(f"{rdata.preference} {rdata.exchange}")
                elif rtype == "TXT":
                    values.append(b"".join(rdata.strings).decode("utf-8", "replace"))
                else:
                    values.append(str(rdata).rstrip("."))
            setattr(records, rtype.lower(), values)
        except dns.resolver.NoAnswer:
            continue
        except dns.resolver.NXDOMAIN:
            records.errors[rtype] = "Domain does not exist (NXDOMAIN)"
            break
        except dns.exception.Timeout:
            records.errors[rtype] = "DNS query timed out"
        except dns.exception.DNSException as exc:
            records.errors[rtype] = str(exc)

    return records


def reverse_lookup(ip: str, timeout: float = 3.0) -> str:
    """Perform a reverse DNS (PTR) lookup for ``ip``."""
    resolver = dns.resolver.Resolver()
    resolver.timeout = timeout
    resolver.lifetime = timeout
    try:
        rev_name = dns.reversename.from_address(ip)
        answer = resolver.resolve(rev_name, "PTR")
        return str(answer[0]).rstrip(".")
    except dns.resolver.NXDOMAIN as exc:
        raise DnsLookupError(f"No PTR record found for {ip}") from exc
    except dns.exception.Timeout as exc:
        raise DnsLookupError(f"Reverse DNS lookup for {ip} timed out") from exc
    except dns.exception.DNSException as exc:
        raise DnsLookupError(f"Reverse DNS lookup failed: {exc}") from exc
