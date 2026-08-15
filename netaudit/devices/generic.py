"""Generic (vendor-unknown) device command set.

Used as a fallback when the device type cannot be determined, or was
explicitly set to 'generic'. Only issues the bare minimum commonly
supported read-only commands.
"""

from __future__ import annotations

DEVICE_TYPE = "generic"

# Read-only only. NetAudit never issues configuration/change commands.
INFO_COMMANDS: dict[str, str] = {
    "version": "show version",
}


def collect_info(connection) -> dict[str, str]:
    """Run the generic info commands and return {label: raw_output}."""
    output: dict[str, str] = {}
    for label, command in INFO_COMMANDS.items():
        try:
            output[label] = connection.send_command(command)
        except Exception as exc:  # noqa: BLE001
            output[label] = f"[error running '{command}': {exc}]"
    return output
