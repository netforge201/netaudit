"""Shared pytest fixtures for the NetAudit test suite."""

from __future__ import annotations

import pytest


@pytest.fixture
def cli_runner():
    """A Typer/Click CliRunner for invoking the CLI in-process."""
    from typer.testing import CliRunner

    return CliRunner()
