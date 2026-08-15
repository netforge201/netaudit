"""Tests for netaudit.scanner.tcp - uses a real local TCP socket, no
external network access required.
"""

from __future__ import annotations

import socket

import pytest

from netaudit.scanner.tcp import check_port, scan_ports


@pytest.fixture
def local_listening_port():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]
    yield port
    srv.close()


def test_check_port_open(local_listening_port):
    result = check_port("127.0.0.1", local_listening_port, timeout=0.5)
    assert result.state == "open"
    assert result.port == local_listening_port


def test_check_port_closed():
    # Bind and immediately close to get a port that's very likely free/closed.
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    port = srv.getsockname()[1]
    srv.close()

    result = check_port("127.0.0.1", port, timeout=0.5)
    assert result.state == "closed"


def test_scan_ports_preserves_order(local_listening_port):
    ports = [local_listening_port, local_listening_port + 1, local_listening_port + 2]
    results = scan_ports("127.0.0.1", ports, timeout=0.3, workers=5)
    assert [r.port for r in results] == ports
    assert results[0].state == "open"


def test_check_port_service_name_lookup(local_listening_port):
    result = check_port("127.0.0.1", 22, timeout=0.1)
    assert result.service == "SSH"
