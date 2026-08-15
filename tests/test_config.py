"""Tests for netaudit.config.settings."""

from __future__ import annotations

from pathlib import Path

import pytest

from netaudit.config.settings import (
    NetAuditSettings,
    init_config,
    load_settings,
    load_yaml_config,
)


def test_load_settings_defaults_when_no_file(tmp_path: Path):
    settings = load_settings(tmp_path / "does-not-exist.yaml")
    assert isinstance(settings, NetAuditSettings)
    assert settings.defaults.timeout == 2.0
    assert settings.defaults.workers == 50
    assert 22 in settings.scanner.default_ports


def test_load_yaml_config_missing_file_returns_empty(tmp_path: Path):
    assert load_yaml_config(tmp_path / "missing.yaml") == {}


def test_load_yaml_config_invalid_yaml_returns_empty(tmp_path: Path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("{ this: is not: valid yaml ][")
    assert load_yaml_config(bad) == {}


def test_load_settings_merges_yaml_overrides(tmp_path: Path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("defaults:\n  timeout: 5\n  workers: 10\n")
    settings = load_settings(config_file)
    assert settings.defaults.timeout == 5
    assert settings.defaults.workers == 10


def test_init_config_creates_file(tmp_path: Path):
    path = tmp_path / "netaudit" / "config.yaml"
    result = init_config(path)
    assert result == path
    assert path.exists()
    assert "defaults:" in path.read_text()


def test_init_config_refuses_overwrite_without_force(tmp_path: Path):
    path = tmp_path / "config.yaml"
    init_config(path)
    with pytest.raises(FileExistsError):
        init_config(path)


def test_init_config_force_overwrites(tmp_path: Path):
    path = tmp_path / "config.yaml"
    init_config(path)
    path.write_text("corrupted")
    init_config(path, force=True)
    assert "defaults:" in path.read_text()
