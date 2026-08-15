"""Juniper Junos read-only command set."""

from __future__ import annotations

DEVICE_TYPE = "juniper_junos"

INFO_COMMANDS: dict[str, str] = {
    "version": "show version",
    "interfaces_terse": "show interfaces terse",
    "routes": "show route",
    "arp": "show arp",
}


def collect_info(connection) -> dict[str, str]:
    """Run the standard Junos read-only 'show' commands."""
    output: dict[str, str] = {}
    for label, command in INFO_COMMANDS.items():
        try:
            output[label] = connection.send_command(command)
        except Exception as exc:  # noqa: BLE001
            output[label] = f"[error running '{command}': {exc}]"
    return output
