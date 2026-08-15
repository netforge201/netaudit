"""Tests for netaudit.utils.validators."""

from __future__ import annotations

import pytest

from netaudit.utils.validators import (
    MAX_SCAN_HOSTS,
    ValidationError,
    parse_cidr,
    parse_ports,
    validate_ip,
    validate_target,
)


class TestValidateIp:
    def test_valid_ipv4(self):
        assert validate_ip("192.168.1.1") == "192.168.1.1"

    def test_valid_ipv6(self):
        assert validate_ip("::1") == "::1"

    def test_invalid_ip_raises(self):
        with pytest.raises(ValidationError):
            validate_ip("not-an-ip")

    def test_invalid_ip_out_of_range_raises(self):
        with pytest.raises(ValidationError):
            validate_ip("999.999.999.999")


class TestValidateTarget:
    def test_ip_target(self):
        assert validate_target("10.0.0.1") == "10.0.0.1"

    def test_hostname_target(self):
        assert validate_target("example.com") == "example.com"

    def test_hostname_with_subdomain(self):
        assert validate_target("router.lab.example.com") == "router.lab.example.com"

    def test_invalid_target_raises(self):
        with pytest.raises(ValidationError):
            validate_target("not a hostname!!")


class TestParseCidr:
    def test_valid_slash_24(self):
        net = parse_cidr("192.168.1.0/24")
        assert net.num_addresses == 256

    def test_bare_ip_becomes_single_host_network(self):
        net = parse_cidr("192.168.1.5")
        assert net.num_addresses == 1

    def test_invalid_cidr_raises(self):
        with pytest.raises(ValidationError):
            parse_cidr("not-a-network")

    def test_oversized_network_rejected(self):
        with pytest.raises(ValidationError, match="exceeds the safety limit"):
            parse_cidr("0.0.0.0/0")

    def test_boundary_network_accepted(self):
        # A /16 has 65536 addresses, right at MAX_SCAN_HOSTS.
        net = parse_cidr("10.0.0.0/16")
        assert net.num_addresses == MAX_SCAN_HOSTS


class TestParsePorts:
    def test_single_ports(self):
        assert parse_ports("22,80,443").ports == [22, 80, 443]

    def test_range(self):
        assert parse_ports("1-5").ports == [1, 2, 3, 4, 5]

    def test_mixed(self):
        assert parse_ports("22,80,1000-1002").ports == [22, 80, 1000, 1001, 1002]

    def test_dedup_and_sort(self):
        assert parse_ports("80,22,80,22").ports == [22, 80]

    def test_invalid_port_raises(self):
        with pytest.raises(ValidationError):
            parse_ports("99999")

    def test_zero_port_raises(self):
        with pytest.raises(ValidationError):
            parse_ports("0")

    def test_invalid_range_raises(self):
        with pytest.raises(ValidationError):
            parse_ports("100-50")

    def test_non_numeric_raises(self):
        with pytest.raises(ValidationError):
            parse_ports("abc")

    def test_empty_spec_raises(self):
        with pytest.raises(ValidationError):
            parse_ports("")
