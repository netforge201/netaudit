"""Individual, independent diagnostic check functions used by 'netaudit doctor'.

Each check returns a CheckResult. Checks that cannot be performed (e.g.
because SSH access wasn't provided, or the target isn't a routable
device) are marked as 'skipped' rather than faked as failures.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CheckStatus(StrEnum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"


@dataclass
class CheckResult:
    name: str
    status: CheckStatus
    message: str
    detail: str | None = None


def reachability_check(target: str, timeout: float = 2.0) -> CheckResult:
    from netaudit.scanner.icmp import ping

    result = ping(target, count=4, timeout=timeout)
    if result.reachable and result.packet_loss_pct == 0:
        return CheckResult("Reachability", CheckStatus.PASS,
                            f"Host is reachable (avg {result.avg_ms} ms)")
    if result.reachable:
        return CheckResult("Reachability", CheckStatus.WARN,
                            f"Host reachable but {result.packet_loss_pct}% packet loss")
    return CheckResult("Reachability", CheckStatus.FAIL,
                        result.error or "Host is not reachable")


def latency_check(target: str, timeout: float = 2.0, warn_ms: float = 100.0) -> CheckResult:
    from netaudit.scanner.icmp import ping

    result = ping(target, count=4, timeout=timeout)
    if not result.reachable or result.avg_ms is None:
        return CheckResult("Latency", CheckStatus.SKIP, "Host unreachable, latency unknown")
    if result.avg_ms > warn_ms:
        return CheckResult("Latency", CheckStatus.WARN,
                            f"High latency: {result.avg_ms} ms (threshold {warn_ms} ms)")
    return CheckResult("Latency", CheckStatus.PASS, f"{result.avg_ms} ms average")


def packet_loss_check(target: str, timeout: float = 2.0) -> CheckResult:
    from netaudit.scanner.icmp import ping

    result = ping(target, count=10, timeout=timeout)
    if result.packets_received == 0:
        return CheckResult("Packet loss", CheckStatus.SKIP, "No replies received")
    if result.packet_loss_pct > 0:
        return CheckResult("Packet loss", CheckStatus.WARN,
                            f"{result.packet_loss_pct}% packet loss detected")
    return CheckResult("Packet loss", CheckStatus.PASS, "0% packet loss")


def dns_check(target: str, timeout: float = 3.0) -> CheckResult:
    import ipaddress

    from netaudit.network.dns import reverse_lookup

    try:
        ipaddress.ip_address(target)
    except ValueError:
        return CheckResult("DNS", CheckStatus.SKIP, "Target is not an IP; skipping reverse DNS")

    try:
        name = reverse_lookup(target, timeout=timeout)
        return CheckResult("DNS", CheckStatus.PASS, f"Reverse DNS resolves to {name}")
    except Exception as exc:  # noqa: BLE001
        return CheckResult("DNS", CheckStatus.WARN, f"No reverse DNS record: {exc}")


def ssh_check(target: str, port: int = 22, timeout: float = 2.0) -> CheckResult:
    from netaudit.scanner.tcp import check_port

    result = check_port(target, port, timeout=timeout)
    if result.state == "open":
        return CheckResult("SSH", CheckStatus.PASS, f"Port {port}/tcp open")
    return CheckResult("SSH", CheckStatus.WARN, f"Port {port}/tcp is {result.state}")


def http_check(target: str, timeout: float = 3.0) -> CheckResult:
    from netaudit.network.latency import check_http

    result = check_http(f"http://{target}", timeout=timeout)
    if result.reachable:
        return CheckResult("HTTP", CheckStatus.PASS, f"HTTP {result.status_code}")
    return CheckResult("HTTP", CheckStatus.SKIP, result.error or "HTTP not reachable")


def https_check(target: str, timeout: float = 3.0) -> CheckResult:
    from netaudit.network.latency import check_http

    result = check_http(f"https://{target}", timeout=timeout)
    if result.reachable:
        return CheckResult("HTTPS", CheckStatus.PASS, f"HTTP {result.status_code}")
    return CheckResult("HTTPS", CheckStatus.SKIP, result.error or "HTTPS not reachable")


def open_services_check(target: str, timeout: float = 1.0) -> CheckResult:
    from netaudit.scanner.tcp import scan_ports
    from netaudit.utils.formatting import COMMON_TCP_PORTS

    results = scan_ports(target, COMMON_TCP_PORTS, timeout=timeout, workers=20)
    open_ports = [r for r in results if r.state == "open"]
    if not open_ports:
        return CheckResult("Open services", CheckStatus.WARN,
                            "No common services detected open")
    names = ", ".join(f"{p.port}/{p.service}" for p in open_ports)
    return CheckResult("Open services", CheckStatus.PASS, f"Detected: {names}")
