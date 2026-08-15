"""Netmiko-based device connection handling with safe credential resolution.

Credentials are NEVER hardcoded or written to disk in plaintext by this
module. They are resolved, in order, from:

1. Explicit CLI arguments (only for username/device-type/port; passwords
   passed on the command line are discouraged and generate a warning
   upstream in the CLI layer)
2. Environment variables: NETAUDIT_USERNAME / NETAUDIT_PASSWORD
3. A local .env file (loaded via python-dotenv if present)
4. An interactive, hidden prompt (getpass)
"""
from __future__ import annotations

import getpass
import os
from contextlib import suppress
from dataclasses import dataclass

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass

try:
    from netmiko import ConnectHandler
    from netmiko.exceptions import (
        NetmikoAuthenticationException,
        NetmikoTimeoutException,
    )

    NETMIKO_AVAILABLE = True
except ImportError:  # pragma: no cover
    NETMIKO_AVAILABLE = False


class DeviceConnectionError(RuntimeError):
    """Raised when a device connection cannot be established."""


class DeviceAuthenticationError(DeviceConnectionError):
    """Raised specifically on authentication failure (bad credentials)."""


class MissingDependencyError(RuntimeError):
    """Raised when Netmiko is not installed."""


SUPPORTED_DEVICE_TYPES = {
    "cisco_ios": "Cisco IOS/IOS-XE",
    "cisco_nxos": "Cisco NX-OS",
    "cisco_xr": "Cisco IOS-XR",
    "juniper_junos": "Juniper Junos",
    "arista_eos": "Arista EOS",
    "generic": "Generic/unknown (best-effort)",
}


@dataclass
class DeviceCredentials:
    username: str
    password: str
    secret: str | None = None


def resolve_credentials(
    username: str | None = None,
    password: str | None = None,
    interactive: bool = True,
) -> DeviceCredentials:
    """Resolve device credentials without ever writing them to disk.

    Precedence: explicit args > environment variables > interactive prompt.
    """
    resolved_user = username or os.environ.get("NETAUDIT_USERNAME")
    resolved_pass = password or os.environ.get("NETAUDIT_PASSWORD")

    if not resolved_user:
        if not interactive:
            raise DeviceConnectionError(
                "No username provided. Set NETAUDIT_USERNAME or pass --username."
            )
        resolved_user = input("Username: ").strip()

    if not resolved_pass:
        if not interactive:
            raise DeviceConnectionError(
                "No password provided. Set NETAUDIT_PASSWORD or pass --password."
            )
        resolved_pass = getpass.getpass("Password: ")

    if not resolved_user or not resolved_pass:
        raise DeviceConnectionError("Username and password are both required.")

    return DeviceCredentials(username=resolved_user, password=resolved_pass)


def connect(
    host: str,
    device_type: str,
    credentials: DeviceCredentials,
    port: int = 22,
    timeout: float = 10.0,
):
    """Open a Netmiko SSH connection to a network device.

    Returns a live Netmiko connection handler. Caller is responsible for
    calling ``.disconnect()`` (a context-manager wrapper is provided by
    ``device_session`` below).
    """
    if not NETMIKO_AVAILABLE:
        raise MissingDependencyError(
            "Netmiko is not installed. Install it with: pip install netmiko"
        )

    params = {
        "device_type": device_type,
        "host": host,
        "username": credentials.username,
        "password": credentials.password,
        "port": port,
        "timeout": timeout,
        "fast_cli": False,
    }
    if credentials.secret:
        params["secret"] = credentials.secret

    try:
        return ConnectHandler(**params)
    except NetmikoAuthenticationException as exc:
        raise DeviceAuthenticationError(
            f"Authentication failed for {credentials.username}@{host}"
        ) from exc
    except NetmikoTimeoutException as exc:
        raise DeviceConnectionError(
            f"Connection to {host}:{port} timed out"
        ) from exc
    except Exception as exc:  # noqa: BLE001 - surface real connection errors
        raise DeviceConnectionError(f"Failed to connect to {host}: {exc}") from exc


class device_session:
    """Context manager wrapping a Netmiko connection for safe cleanup."""

    def __init__(self, host: str, device_type: str, credentials: DeviceCredentials,
                 port: int = 22, timeout: float = 10.0):
        self.host = host
        self.device_type = device_type
        self.credentials = credentials
        self.port = port
        self.timeout = timeout
        self.connection = None

    def __enter__(self):
        self.connection = connect(
            self.host, self.device_type, self.credentials, self.port, self.timeout
        )
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection is not None:
            with suppress(Exception):
                self.connection.disconnect()
        return False
