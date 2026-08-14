"""Tests for netaudit.network.routing (traceroute) - mocks subprocess."""
from __future__ import annotations

import subprocess
from unittest.mock import patch

from netaudit.network.routing import traceroute

LINUX_TRACEROUTE_OUTPUT = """\
traceroute to 8.8.8.8 (8.8.8.8), 30 hops max, 60 byte packets
 1  192.168.1.1 (192.168.1.1)  1.234 ms  1.100 ms  1.050 ms
 2  10.10.0.1 (10.10.0.1)  8.400 ms  8.200 ms  8.100 ms
 3  * * *
 4  8.8.8.8 (8.8.8.8)  25.300 ms  25.100 ms  25.000 ms
"""


def _mock_completed(stdout: str) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=["traceroute"], returncode=0, stdout=stdout, stderr="")


@patch("netaudit.network.routing.shutil.which", return_value="/usr/bin/traceroute")
@patch("netaudit.network.routing.platform.system", return_value="Linux")
@patch("netaudit.network.routing.subprocess.run")
def test_traceroute_parses_hops(mock_run, mock_system, mock_which):
    mock_run.return_value = _mock_completed(LINUX_TRACEROUTE_OUTPUT)
    result = traceroute("8.8.8.8", max_hops=30, timeout=2)

    assert len(result.hops) == 4
    assert result.hops[0].address == "192.168.1.1"
    assert result.hops[0].rtt_ms == [1.234, 1.100, 1.050]
    assert result.hops[2].address is None  # "* * *" hop
    assert result.reached is True


@patch("netaudit.network.routing.shutil.which", return_value=None)
@patch("netaudit.network.routing.platform.system", return_value="Linux")
def test_traceroute_binary_missing(mock_system, mock_which):
    result = traceroute("8.8.8.8")
    assert result.hops == []
    assert result.error is not None
    assert "not found" in result.error


@patch("netaudit.network.routing.shutil.which", return_value="/usr/bin/traceroute")
@patch("netaudit.network.routing.platform.system", return_value="Linux")
@patch("netaudit.network.routing.subprocess.run",
       side_effect=subprocess.TimeoutExpired("traceroute", 5))
def test_traceroute_timeout(mock_run, mock_system, mock_which):
    result = traceroute("8.8.8.8")
    assert result.error is not None
    assert "timed out" in result.error
