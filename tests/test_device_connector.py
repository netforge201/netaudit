"""Tests for netaudit.devices.connector - mocks Netmiko entirely so no
real SSH connections or credentials are needed.
"""
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from netaudit.devices.connector import (
    DeviceAuthenticationError,
    DeviceConnectionError,
    DeviceCredentials,
    connect,
    resolve_credentials,
)


class TestResolveCredentials:
    def test_uses_explicit_args(self):
        creds = resolve_credentials(username="admin", password="secret", interactive=False)
        assert creds.username == "admin"
        assert creds.password == "secret"

    def test_uses_environment_variables(self, monkeypatch):
        monkeypatch.setenv("NETAUDIT_USERNAME", "envuser")
        monkeypatch.setenv("NETAUDIT_PASSWORD", "envpass")
        creds = resolve_credentials(interactive=False)
        assert creds.username == "envuser"
        assert creds.password == "envpass"

    def test_explicit_args_take_precedence_over_env(self, monkeypatch):
        monkeypatch.setenv("NETAUDIT_USERNAME", "envuser")
        monkeypatch.setenv("NETAUDIT_PASSWORD", "envpass")
        creds = resolve_credentials(username="cliuser", password="clipass", interactive=False)
        assert creds.username == "cliuser"
        assert creds.password == "clipass"

    def test_raises_without_credentials_when_noninteractive(self, monkeypatch):
        monkeypatch.delenv("NETAUDIT_USERNAME", raising=False)
        monkeypatch.delenv("NETAUDIT_PASSWORD", raising=False)
        with pytest.raises(DeviceConnectionError):
            resolve_credentials(interactive=False)

    def test_never_logs_password(self, monkeypatch, capsys):
        monkeypatch.setenv("NETAUDIT_USERNAME", "admin")
        monkeypatch.setenv("NETAUDIT_PASSWORD", "super-secret-value")
        resolve_credentials(interactive=False)
        captured = capsys.readouterr()
        assert "super-secret-value" not in captured.out
        assert "super-secret-value" not in captured.err


class TestConnect:
    @patch("netaudit.devices.connector.NETMIKO_AVAILABLE", True)
    @patch("netaudit.devices.connector.ConnectHandler")
    def test_connect_success(self, mock_handler):
        mock_conn = MagicMock()
        mock_handler.return_value = mock_conn

        creds = DeviceCredentials(username="admin", password="secret")
        result = connect("10.0.0.1", "cisco_ios", creds)

        assert result is mock_conn
        mock_handler.assert_called_once()
        call_kwargs = mock_handler.call_args.kwargs
        assert call_kwargs["host"] == "10.0.0.1"
        assert call_kwargs["username"] == "admin"

    @patch("netaudit.devices.connector.NETMIKO_AVAILABLE", True)
    @patch("netaudit.devices.connector.ConnectHandler")
    def test_connect_auth_failure(self, mock_handler):
        from netmiko.exceptions import NetmikoAuthenticationException

        mock_handler.side_effect = NetmikoAuthenticationException("bad creds")
        creds = DeviceCredentials(username="admin", password="wrong")

        with pytest.raises(DeviceAuthenticationError):
            connect("10.0.0.1", "cisco_ios", creds)

    @patch("netaudit.devices.connector.NETMIKO_AVAILABLE", True)
    @patch("netaudit.devices.connector.ConnectHandler")
    def test_connect_timeout(self, mock_handler):
        from netmiko.exceptions import NetmikoTimeoutException

        mock_handler.side_effect = NetmikoTimeoutException("timed out")
        creds = DeviceCredentials(username="admin", password="secret")

        with pytest.raises(DeviceConnectionError):
            connect("10.0.0.1", "cisco_ios", creds)

    @patch("netaudit.devices.connector.NETMIKO_AVAILABLE", False)
    def test_connect_missing_dependency(self):
        from netaudit.devices.connector import MissingDependencyError

        creds = DeviceCredentials(username="admin", password="secret")
        with pytest.raises(MissingDependencyError):
            connect("10.0.0.1", "cisco_ios", creds)
