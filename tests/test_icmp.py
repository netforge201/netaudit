"""Tests for netaudit.scanner.icmp - mocks the subprocess call so no
real network access or root privileges are required.
"""

from __future__ import annotations

import subprocess
from unittest.mock import patch

from netaudit.scanner.icmp import os_hint_from_ttl, ping

LINUX_PING_OUTPUT = """\
PING 127.0.0.1 (127.0.0.1) 56(84) bytes of data.
64 bytes from 127.0.0.1: icmp_seq=1 ttl=64 time=0.032 ms
64 bytes from 127.0.0.1: icmp_seq=2 ttl=64 time=0.045 ms

--- 127.0.0.1 ping statistics ---
2 packets transmitted, 2 received, 0% packet loss, time 1001ms
rtt min/avg/max/mdev = 0.032/0.038/0.045/0.006 ms
"""

LINUX_PING_UNREACHABLE = """\
PING 10.255.255.1 (10.255.255.1) 56(84) bytes of data.

--- 10.255.255.1 ping statistics ---
4 packets transmitted, 0 received, 100% packet loss, time 3060ms
"""


def _mock_completed(stdout: str, stderr: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=["ping"], returncode=0, stdout=stdout, stderr=stderr)


@patch("netaudit.scanner.icmp.shutil.which", return_value="/bin/ping")
@patch("netaudit.scanner.icmp.subprocess.run")
def test_ping_success_parses_stats(mock_run, mock_which):
    mock_run.return_value = _mock_completed(LINUX_PING_OUTPUT)
    result = ping("127.0.0.1", count=2, timeout=1)

    assert result.reachable is True
    assert result.packets_received == 2
    assert result.packet_loss_pct == 0.0
    assert result.ttl == 64
    assert result.min_ms == 0.032
    assert result.max_ms == 0.045


@patch("netaudit.scanner.icmp.shutil.which", return_value="/bin/ping")
@patch("netaudit.scanner.icmp.subprocess.run")
def test_ping_unreachable(mock_run, mock_which):
    mock_run.return_value = _mock_completed(LINUX_PING_UNREACHABLE)
    result = ping("10.255.255.1", count=4, timeout=1)

    assert result.reachable is False
    assert result.packet_loss_pct == 100.0
    assert result.error is not None


@patch("netaudit.scanner.icmp.shutil.which", return_value=None)
def test_ping_binary_missing(mock_which):
    result = ping("127.0.0.1")
    assert result.reachable is False
    assert "not found" in result.error


@patch("netaudit.scanner.icmp.shutil.which", return_value="/bin/ping")
@patch("netaudit.scanner.icmp.subprocess.run", side_effect=subprocess.TimeoutExpired("ping", 5))
def test_ping_subprocess_timeout(mock_run, mock_which):
    result = ping("127.0.0.1", count=1, timeout=1)
    assert result.reachable is False
    assert "timed out" in result.error


def test_os_hint_from_ttl():
    assert "Linux" in os_hint_from_ttl(64)
    assert "Windows" in os_hint_from_ttl(128)
    assert "router" in os_hint_from_ttl(255)
    assert os_hint_from_ttl(None) is None
