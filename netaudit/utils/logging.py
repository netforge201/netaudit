"""Logging setup for NetAudit.

All logging goes to stderr so that stdout stays clean for command
output (important for use in shell pipelines and automation).
"""
from __future__ import annotations

import logging
import sys

_LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
_DATE_FORMAT = "%H:%M:%S"


def setup_logging(verbose: bool = False, debug: bool = False) -> logging.Logger:
    """Configure the root ``netaudit`` logger to write to stderr.

    Args:
        verbose: enable INFO level logging.
        debug: enable DEBUG level logging (implies verbose).

    Returns:
        The configured ``netaudit`` logger.
    """
    logger = logging.getLogger("netaudit")
    logger.handlers.clear()

    level = logging.WARNING
    if debug:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO

    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the ``netaudit`` namespace."""
    return logging.getLogger(f"netaudit.{name}")
