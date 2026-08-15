"""Tests for netaudit.network.interfaces - runs against real psutil data
for this machine (no network access or elevated privileges required).
"""

from __future__ import annotations

from netaudit.network.interfaces import list_interfaces


def test_list_interfaces_returns_at_least_loopback():
    interfaces = list_interfaces()
    names = [i.name for i in interfaces]
    # Every POSIX system has a loopback interface, though its exact name
    # varies (lo, lo0, Loopback Pseudo-Interface 1, ...).
    assert len(interfaces) > 0
    assert any("lo" in n.lower() for n in names)


def test_interfaces_sorted_by_name():
    interfaces = list_interfaces()
    names = [i.name for i in interfaces]
    assert names == sorted(names)


def test_interface_fields_have_correct_types():
    for iface in list_interfaces():
        assert isinstance(iface.name, str)
        assert isinstance(iface.is_up, bool)
        assert isinstance(iface.ipv4, list)
        assert isinstance(iface.ipv6, list)
