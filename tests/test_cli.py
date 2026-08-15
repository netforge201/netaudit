"""CLI-level tests using Typer's CliRunner.

These exercise argument parsing, help text, and error handling end to
end. Anything that would touch the real network is mocked.
"""

from __future__ import annotations

import re
from unittest.mock import patch

from netaudit import __version__
from netaudit.cli import app


def plain(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def test_version_flag(cli_runner):
    result = cli_runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_version_command(cli_runner):
    result = cli_runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_no_args_shows_banner(cli_runner):
    result = cli_runner.invoke(app, [])
    assert result.exit_code == 0
    assert "NetAudit" in result.output


def test_help_flag(cli_runner):
    result = cli_runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "scan" in result.output
    assert "doctor" in result.output


def test_scan_help(cli_runner):
    result = cli_runner.invoke(app, ["scan", "--help"])
    assert result.exit_code == 0
    assert "--ports" in plain(result.output)


def test_ports_help(cli_runner):
    result = cli_runner.invoke(app, ["ports", "--help"])
    assert result.exit_code == 0
    assert "--range" in plain(result.output)


def test_doctor_help(cli_runner):
    result = cli_runner.invoke(app, ["doctor", "--help"])
    assert result.exit_code == 0


def test_snapshot_help(cli_runner):
    result = cli_runner.invoke(app, ["snapshot", "--help"])
    assert result.exit_code == 0
    assert "--list" in plain(result.output)


def test_diff_help(cli_runner):
    result = cli_runner.invoke(app, ["diff", "--help"])
    assert result.exit_code == 0


def test_report_help(cli_runner):
    result = cli_runner.invoke(app, ["report", "--help"])
    assert result.exit_code == 0


def test_device_help(cli_runner):
    result = cli_runner.invoke(app, ["device", "--help"])
    assert result.exit_code == 0
    assert "connect" in result.output
    assert "info" in result.output


def test_invalid_cidr_exits_with_code_2(cli_runner):
    result = cli_runner.invoke(app, ["scan", "not-a-network"])
    assert result.exit_code == 2


def test_invalid_target_for_host_exits_with_code_2(cli_runner):
    result = cli_runner.invoke(app, ["host", "not a valid host!!"])
    assert result.exit_code == 2


def test_scan_oversized_cidr_rejected(cli_runner):
    result = cli_runner.invoke(app, ["scan", "0.0.0.0/0"])
    assert result.exit_code == 2
    assert "exceeds the safety limit" in result.output


def test_scan_options_after_argument_are_parsed(cli_runner):
    # Regression test for the Click Group argument-consumption bug:
    # options placed AFTER the positional target must still be parsed.
    with patch("netaudit.scanner.discovery.scan_network") as mock_scan:
        from netaudit.scanner.discovery import ScanSummary

        mock_scan.return_value = ScanSummary(
            hosts=[], discovered=0, online=0, offline=0, duration_s=0.0
        )
        result = cli_runner.invoke(app, ["scan", "192.168.1.0/30", "--ports", "22,80", "--quiet"])
        assert result.exit_code == 0
        # Confirm --ports was actually parsed and passed through (4th positional arg).
        _, _kwargs_or_args = mock_scan.call_args, mock_scan.call_args.args
        assert mock_scan.call_args.args[3] == [22, 80]


def test_config_show(cli_runner):
    result = cli_runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0


def test_config_init_writes_file(cli_runner, tmp_path):
    target = tmp_path / "netaudit" / "config.yaml"
    with patch("netaudit.commands.config.init_config") as mock_init:
        mock_init.return_value = target
        result = cli_runner.invoke(app, ["config", "init"])
        assert result.exit_code == 0
        mock_init.assert_called_once()


def test_config_init_refuses_overwrite_without_force(cli_runner, tmp_path):
    target = tmp_path / "config.yaml"
    with patch("netaudit.commands.config.init_config", side_effect=FileExistsError(str(target))):
        result = cli_runner.invoke(app, ["config", "init"])
        assert result.exit_code == 1
