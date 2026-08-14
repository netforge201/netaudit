"""Tests for netaudit.network.dns - mocks dns.resolver so no real DNS
queries are made.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import dns.exception
import dns.resolver

from netaudit.network.dns import DnsLookupError, lookup, reverse_lookup


class FakeAnswer(list):
    pass


def _make_a_record(addr: str):
    rdata = MagicMock()
    rdata.__str__.return_value = addr
    return rdata


@patch("netaudit.network.dns.dns.resolver.Resolver")
def test_lookup_returns_a_records(mock_resolver_cls):
    resolver = mock_resolver_cls.return_value

    def resolve_side_effect(name, rtype):
        if rtype == "A":
            return FakeAnswer([_make_a_record("93.184.216.34")])
        raise dns.resolver.NoAnswer()

    resolver.resolve.side_effect = resolve_side_effect

    records = lookup("example.com")
    assert records.a == ["93.184.216.34"]
    assert records.mx == []


@patch("netaudit.network.dns.dns.resolver.Resolver")
def test_lookup_nxdomain_records_error(mock_resolver_cls):
    resolver = mock_resolver_cls.return_value
    resolver.resolve.side_effect = dns.resolver.NXDOMAIN()

    records = lookup("this-domain-should-not-exist-netaudit-test.invalid")
    assert "A" in records.errors
    assert "NXDOMAIN" in records.errors["A"]


@patch("netaudit.network.dns.dns.resolver.Resolver")
def test_lookup_timeout_records_error(mock_resolver_cls):
    resolver = mock_resolver_cls.return_value
    resolver.resolve.side_effect = dns.exception.Timeout()

    records = lookup("example.com")
    assert "A" in records.errors


@patch("netaudit.network.dns.dns.resolver.Resolver")
def test_reverse_lookup_success(mock_resolver_cls):
    resolver = mock_resolver_cls.return_value
    ptr = MagicMock()
    ptr.__str__.return_value = "dns.google."
    resolver.resolve.return_value = [ptr]

    name = reverse_lookup("8.8.8.8")
    assert name == "dns.google"


@patch("netaudit.network.dns.dns.resolver.Resolver")
def test_reverse_lookup_nxdomain_raises(mock_resolver_cls):
    resolver = mock_resolver_cls.return_value
    resolver.resolve.side_effect = dns.resolver.NXDOMAIN()

    try:
        reverse_lookup("192.0.2.123")
        assert False, "should have raised"
    except DnsLookupError:
        pass
