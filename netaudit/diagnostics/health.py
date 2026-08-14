"""Orchestrates the full 'netaudit doctor' health-check run.

Runs network-layer checks (always) plus device-layer checks (only if
credentials/device access were provided and a connection succeeds).
Produces a weighted health score out of 100 based on pass/warn/fail
results. Checks that could not be performed are excluded from
scoring entirely, per project requirements (never fake results).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from netaudit.diagnostics.checks import (
    CheckResult,
    CheckStatus,
    dns_check,
    http_check,
    https_check,
    latency_check,
    open_services_check,
    packet_loss_check,
    reachability_check,
    ssh_check,
)

_SCORE_WEIGHTS = {
    CheckStatus.PASS: 1.0,
    CheckStatus.WARN: 0.5,
    CheckStatus.FAIL: 0.0,
}


@dataclass
class HealthReport:
    target: str
    checks: list[CheckResult] = field(default_factory=list)
    score: int = 0

    def add(self, result: CheckResult) -> None:
        self.checks.append(result)

    def finalize(self) -> None:
        scored = [c for c in self.checks if c.status != CheckStatus.SKIP]
        if not scored:
            self.score = 0
            return
        total = sum(_SCORE_WEIGHTS[c.status] for c in scored)
        self.score = round(100 * total / len(scored))


def run_network_checks(target: str, timeout: float = 2.0) -> list[CheckResult]:
    """Run the checks that don't require device SSH access."""
    return [
        reachability_check(target, timeout),
        latency_check(target, timeout),
        packet_loss_check(target, timeout),
        dns_check(target, timeout),
        ssh_check(target, timeout=timeout),
        http_check(target, timeout=max(timeout, 3.0)),
        https_check(target, timeout=max(timeout, 3.0)),
        open_services_check(target, timeout),
    ]


def run_device_checks(target: str, device_type: str, credentials) -> list[CheckResult]:
    """Run checks that require an authenticated device SSH session.

    Returns a single-item list with a SKIP result if the connection
    could not be established (e.g. no credentials, auth failure), so
    the caller can surface a clear reason rather than silently omitting
    the checks.
    """
    from netaudit.devices import module_for
    from netaudit.devices.connector import (
        DeviceAuthenticationError,
        DeviceConnectionError,
        MissingDependencyError,
        device_session,
    )
    from netaudit.diagnostics import services as svc
    from netaudit.diagnostics.interfaces import (
        parse_ios_interface_errors,
        parse_ios_interfaces_brief,
    )

    results: list[CheckResult] = []

    try:
        with device_session(target, device_type, credentials) as conn:
            module = module_for(device_type)
            info = module.collect_info(conn)

            # Interfaces
            if "interfaces_brief" in info:
                statuses = parse_ios_interfaces_brief(info["interfaces_brief"])
                down = [s for s in statuses if s.status != "up" and "admin" not in s.status]
                if statuses:
                    if down:
                        results.append(CheckResult(
                            "Interfaces", CheckStatus.WARN,
                            f"{len(down)} interface(s) down: " +
                            ", ".join(s.name for s in down[:5])
                        ))
                    else:
                        results.append(CheckResult(
                            "Interfaces", CheckStatus.PASS,
                            f"All {len(statuses)} interfaces up"
                        ))
                else:
                    results.append(CheckResult(
                        "Interfaces", CheckStatus.SKIP, "Could not parse interface status"
                    ))

            if "interfaces" in info:
                errors = parse_ios_interface_errors(info["interfaces"])
                bad = [e for e in errors if e.input_errors or e.output_errors or e.crc_errors]
                if errors:
                    if bad:
                        results.append(CheckResult(
                            "Interface errors", CheckStatus.WARN,
                            f"Errors detected on {len(bad)} interface(s): " +
                            ", ".join(e.name for e in bad[:5])
                        ))
                    else:
                        results.append(CheckResult(
                            "Interface errors", CheckStatus.PASS, "No interface errors detected"
                        ))

            # CPU / memory / uptime (best effort, IOS-specific)
            if "version" in info:
                health = svc.parse_ios_version(info["version"])
                if health.uptime:
                    results.append(CheckResult("Uptime", CheckStatus.PASS, health.uptime))

            # Routing
            if "routes" in info:
                if svc.has_default_route(info["routes"]):
                    results.append(CheckResult("Default route", CheckStatus.PASS,
                                                "Default route present"))
                else:
                    results.append(CheckResult("Default route", CheckStatus.WARN,
                                                "No default route found"))

            # ARP
            if "arp" in info:
                results.append(CheckResult(
                    "ARP table", CheckStatus.PASS if info["arp"].strip() else CheckStatus.WARN,
                    f"ARP table retrieved ({len(info['arp'].splitlines())} lines)"
                    if info["arp"].strip() else "ARP table is empty"
                ))

            # NTP - only attempt if IOS-family
            try:
                ntp_raw = conn.send_command("show ntp status")
                synced = svc.parse_ntp_status(ntp_raw)
                if synced is True:
                    results.append(CheckResult("NTP", CheckStatus.PASS, "Clock synchronized"))
                elif synced is False:
                    results.append(CheckResult("NTP", CheckStatus.WARN, "Clock not synchronized"))
                else:
                    results.append(CheckResult("NTP", CheckStatus.SKIP, "NTP status unavailable"))
            except Exception:  # noqa: BLE001
                results.append(CheckResult("NTP", CheckStatus.SKIP, "NTP status unavailable"))

            # BGP - best effort
            try:
                bgp_raw = conn.send_command("show ip bgp summary")
                bgp = svc.parse_bgp_summary(bgp_raw)
                if bgp is not None:
                    total, established = bgp
                    if total == 0:
                        results.append(CheckResult("BGP", CheckStatus.SKIP, "No BGP neighbors configured"))
                    elif established < total:
                        results.append(CheckResult(
                            "BGP", CheckStatus.WARN,
                            f"{total - established} of {total} BGP neighbor(s) down"
                        ))
                    else:
                        results.append(CheckResult(
                            "BGP", CheckStatus.PASS, f"All {total} BGP neighbor(s) established"
                        ))
            except Exception:  # noqa: BLE001
                pass  # BGP unsupported/unavailable on this platform - omit silently

            # OSPF - best effort
            try:
                ospf_raw = conn.send_command("show ip ospf neighbor")
                ospf = svc.parse_ospf_neighbors(ospf_raw)
                if ospf is not None:
                    total, full = ospf
                    if total == 0:
                        results.append(CheckResult("OSPF", CheckStatus.SKIP, "No OSPF neighbors configured"))
                    elif full < total:
                        results.append(CheckResult(
                            "OSPF", CheckStatus.WARN,
                            f"{total - full} of {total} OSPF neighbor(s) not Full"
                        ))
                    else:
                        results.append(CheckResult(
                            "OSPF", CheckStatus.PASS, f"All {total} OSPF neighbor(s) Full"
                        ))
            except Exception:  # noqa: BLE001
                pass  # OSPF unsupported/unavailable on this platform - omit silently

    except MissingDependencyError as exc:
        results.append(CheckResult("Device checks", CheckStatus.SKIP, str(exc)))
    except DeviceAuthenticationError as exc:
        results.append(CheckResult("Device checks", CheckStatus.SKIP,
                                    f"Skipped (authentication failed): {exc}"))
    except DeviceConnectionError as exc:
        results.append(CheckResult("Device checks", CheckStatus.SKIP,
                                    f"Skipped (connection failed): {exc}"))

    return results


def run_doctor(
    target: str,
    timeout: float = 2.0,
    device_type: str | None = None,
    credentials=None,
) -> HealthReport:
    """Run the full doctor check suite and compute a health score."""
    report = HealthReport(target=target)
    for check in run_network_checks(target, timeout):
        report.add(check)

    if device_type and credentials:
        for check in run_device_checks(target, device_type, credentials):
            report.add(check)

    report.finalize()
    return report
