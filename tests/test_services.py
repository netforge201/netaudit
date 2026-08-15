"""Tests for netaudit.utils.services (well-known port/service data)."""

from __future__ import annotations

from netaudit.utils.services import COMMON_TCP_PORTS, service_name


def test_known_service_name():
    assert service_name(22) == "SSH"
    assert service_name(443) == "HTTPS"


def test_unknown_service_name():
    assert service_name(59999) == "UNKNOWN"


def test_common_ports_nonempty_and_unique():
    assert len(COMMON_TCP_PORTS) > 0
    assert len(COMMON_TCP_PORTS) == len(set(COMMON_TCP_PORTS))
