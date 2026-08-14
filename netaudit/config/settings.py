"""NetAudit configuration handling.

Configuration is loaded, in increasing order of precedence, from:

1. Built-in defaults
2. ``~/.netaudit/config.yaml``
3. Environment variables (``NETAUDIT_*``)

Credentials (username/password) are NEVER read from the config file -
only from environment variables, a ``.env`` file, or an interactive
prompt (see ``netaudit.devices.connector``).
"""
from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

CONFIG_DIR = Path.home() / ".netaudit"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

DEFAULT_CONFIG_YAML = """\
defaults:
  timeout: 2
  workers: 50

scanner:
  default_ports:
    - 21
    - 22
    - 23
    - 25
    - 53
    - 80
    - 110
    - 139
    - 143
    - 443
    - 445
    - 3306
    - 3389
    - 5432
    - 5900
    - 8080
    - 8443

reports:
  directory: ./reports

snapshots:
  directory: ./snapshots
"""


class DefaultsConfig(BaseModel):
    timeout: float = 2.0
    workers: int = 50


class ScannerConfig(BaseModel):
    default_ports: list[int] = Field(
        default_factory=lambda: [21, 22, 23, 25, 53, 80, 110, 139, 143,
                                  443, 445, 3306, 3389, 5432, 5900, 8080, 8443]
    )


class ReportsConfig(BaseModel):
    directory: str = "./reports"


class SnapshotsConfig(BaseModel):
    directory: str = "./snapshots"


class NetAuditSettings(BaseSettings):
    """Top-level settings object, merged from config.yaml + environment."""

    model_config = SettingsConfigDict(
        env_prefix="NETAUDIT_", env_nested_delimiter="__", extra="ignore"
    )

    defaults: DefaultsConfig = Field(default_factory=DefaultsConfig)
    scanner: ScannerConfig = Field(default_factory=ScannerConfig)
    reports: ReportsConfig = Field(default_factory=ReportsConfig)
    snapshots: SnapshotsConfig = Field(default_factory=SnapshotsConfig)


def load_yaml_config(path: Path = CONFIG_FILE) -> dict:
    """Load raw YAML config from disk, returning {} if missing/invalid."""
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        if not isinstance(data, dict):
            return {}
        return data
    except yaml.YAMLError:
        return {}


def load_settings(path: Path = CONFIG_FILE) -> NetAuditSettings:
    """Load merged settings from YAML config file + environment variables."""
    yaml_data = load_yaml_config(path)
    return NetAuditSettings(**yaml_data)


def init_config(path: Path = CONFIG_FILE, force: bool = False) -> Path:
    """Write the default config file to ``path`` if it doesn't already exist."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        raise FileExistsError(f"Config file already exists at {path}")
    path.write_text(DEFAULT_CONFIG_YAML, encoding="utf-8")
    return path
