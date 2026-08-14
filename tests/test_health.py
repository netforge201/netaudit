"""Tests for netaudit.diagnostics.health scoring logic."""
from __future__ import annotations

from unittest.mock import patch

from netaudit.diagnostics.checks import CheckResult, CheckStatus
from netaudit.diagnostics.health import HealthReport, run_doctor


def test_health_report_score_all_pass():
    report = HealthReport(target="10.0.0.1")
    report.add(CheckResult("A", CheckStatus.PASS, "ok"))
    report.add(CheckResult("B", CheckStatus.PASS, "ok"))
    report.finalize()
    assert report.score == 100


def test_health_report_score_mixed():
    report = HealthReport(target="10.0.0.1")
    report.add(CheckResult("A", CheckStatus.PASS, "ok"))
    report.add(CheckResult("B", CheckStatus.FAIL, "bad"))
    report.finalize()
    assert report.score == 50


def test_health_report_score_excludes_skipped():
    report = HealthReport(target="10.0.0.1")
    report.add(CheckResult("A", CheckStatus.PASS, "ok"))
    report.add(CheckResult("B", CheckStatus.SKIP, "n/a"))
    report.finalize()
    assert report.score == 100  # skipped check doesn't count against score


def test_health_report_score_zero_when_all_skipped():
    report = HealthReport(target="10.0.0.1")
    report.add(CheckResult("A", CheckStatus.SKIP, "n/a"))
    report.finalize()
    assert report.score == 0


def test_health_report_warn_counts_as_half():
    report = HealthReport(target="10.0.0.1")
    report.add(CheckResult("A", CheckStatus.WARN, "meh"))
    report.finalize()
    assert report.score == 50


@patch("netaudit.diagnostics.health.run_network_checks")
def test_run_doctor_without_device_only_runs_network_checks(mock_net):
    mock_net.return_value = [CheckResult("Reachability", CheckStatus.PASS, "ok")]
    report = run_doctor("10.0.0.1", timeout=1.0)
    assert len(report.checks) == 1
    assert report.score == 100


@patch("netaudit.diagnostics.health.run_device_checks")
@patch("netaudit.diagnostics.health.run_network_checks")
def test_run_doctor_with_device_runs_both(mock_net, mock_device):
    mock_net.return_value = [CheckResult("Reachability", CheckStatus.PASS, "ok")]
    mock_device.return_value = [CheckResult("Interfaces", CheckStatus.PASS, "ok")]

    report = run_doctor("10.0.0.1", timeout=1.0, device_type="cisco_ios", credentials="fake")
    assert len(report.checks) == 2
    assert report.score == 100
