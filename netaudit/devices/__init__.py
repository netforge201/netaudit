"""Vendor-specific device command modules, dispatched by Netmiko device_type."""
from __future__ import annotations

from netaudit.devices import arista, cisco, generic, juniper

_MODULES = {
    "cisco_ios": cisco,
    "cisco_nxos": cisco,
    "cisco_xr": cisco,
    "juniper_junos": juniper,
    "arista_eos": arista,
    "generic": generic,
}


def module_for(device_type: str):
    """Return the vendor command module for ``device_type``, or generic fallback."""
    return _MODULES.get(device_type, generic)
