"""Tests for Cisco IOS output parsing in netaudit.diagnostics.

These use static, realistic sample output - no live device or network
access required.
"""
from __future__ import annotations

from netaudit.diagnostics import services as svc
from netaudit.diagnostics.interfaces import (
    parse_ios_interface_errors,
    parse_ios_interfaces_brief,
)

SAMPLE_BRIEF = """\
Interface              IP-Address      OK? Method Status                Protocol
GigabitEthernet0/0     192.168.1.1     YES manual up                    up
GigabitEthernet0/1     unassigned      YES unset  administratively down down
GigabitEthernet0/2     10.0.0.1        YES manual down                  down
"""

SAMPLE_INTERFACES = """\
GigabitEthernet0/0 is up, line protocol is up
  Hardware is iGbE, address is 0050.5677.0001
  5 minute input rate 0 bits/sec, 0 packets/sec
     100 packets input, 6000 bytes
     0 input errors, 0 CRC, 0 frame, 0 overrun
     50 packets output, 3000 bytes
     0 output errors, 0 collisions, 0 interface resets
GigabitEthernet0/1 is administratively down, line protocol is down
  Hardware is iGbE, address is 0050.5677.0002
     0 packets input, 0 bytes
     12 input errors, 8 CRC, 0 frame, 0 overrun
     0 packets output, 0 bytes
     3 output errors, 0 collisions, 0 interface resets
"""

SAMPLE_VERSION = """\
Cisco IOS Software, C3560 Software
router uptime is 3 weeks, 2 days, 4 hours, 10 minutes
"""

SAMPLE_ROUTE_WITH_DEFAULT = """\
Gateway of last resort is 192.168.1.1 to network 0.0.0.0

S*    0.0.0.0/0 [1/0] via 192.168.1.1
      10.0.0.0/8 is variably subnetted
"""

SAMPLE_ROUTE_NO_DEFAULT = """\
Gateway of last resort is not set

      10.0.0.0/8 is variably subnetted
"""

SAMPLE_NTP_SYNCED = "Clock is synchronized, stratum 3, reference is 10.0.0.1"
SAMPLE_NTP_UNSYNCED = "Clock is unsynchronized, stratum 16, no reference clock"


def test_parse_interfaces_brief():
    statuses = parse_ios_interfaces_brief(SAMPLE_BRIEF)
    assert len(statuses) == 3
    assert statuses[0].name == "GigabitEthernet0/0"
    assert statuses[0].status == "up"
    assert statuses[1].status == "administratively down"


def test_parse_interface_errors():
    errors = parse_ios_interface_errors(SAMPLE_INTERFACES)
    assert len(errors) == 2
    clean, errored = errors[0], errors[1]
    assert clean.input_errors == 0 and clean.crc_errors == 0
    assert errored.input_errors == 12
    assert errored.crc_errors == 8
    assert errored.output_errors == 3


def test_parse_ios_version_uptime():
    health = svc.parse_ios_version(SAMPLE_VERSION)
    assert "3 weeks" in health.uptime


def test_has_default_route_true():
    assert svc.has_default_route(SAMPLE_ROUTE_WITH_DEFAULT) is True


def test_has_default_route_false():
    assert svc.has_default_route(SAMPLE_ROUTE_NO_DEFAULT) is False


def test_ntp_status_synced():
    assert svc.parse_ntp_status(SAMPLE_NTP_SYNCED) is True


def test_ntp_status_unsynced():
    assert svc.parse_ntp_status(SAMPLE_NTP_UNSYNCED) is False


def test_ntp_status_unsupported_command():
    assert svc.parse_ntp_status("% Invalid input detected at '^' marker.") is None


def test_bgp_summary_no_neighbors_configured():
    assert svc.parse_bgp_summary("% BGP not active") is None


def test_ospf_neighbors_unsupported():
    assert svc.parse_ospf_neighbors("% Invalid input detected") is None
