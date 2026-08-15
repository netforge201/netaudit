"""Cisco IOS/IOS-XE read-only command set."""

from __future__ import annotations

DEVICE_TYPE = "cisco_ios"

INFO_COMMANDS: dict[str, str] = {
    "version": "show version",
    "interfaces_brief": "show ip interface brief",
    "interfaces": "show interfaces",
    "routes": "show ip route",
    "arp": "show arp",
}


def collect_info(connection) -> dict[str, str]:
    """Run the standard Cisco IOS read-only 'show' commands."""
    output: dict[str, str] = {}
    for label, command in INFO_COMMANDS.items():
        try:
            output[label] = connection.send_command(command)
        except Exception as exc:  # noqa: BLE001
            output[label] = f"[error running '{command}': {exc}]"
    return output
