"""Verbose logging package for Sherpa AI.

This package provides various logging implementations for verbose output
in different contexts. It includes loggers for Slack messaging, testing,
and no-op scenarios.

Example:
    >>> from sherpa_ai.verbose_loggers import StorageVerboseLogger
    >>> logger = StorageVerboseLogger()
    >>> logger.log("Test message")
    >>> print(logger.storage)
    ['Test message']
"""

from sherpa_ai.verbose_loggers.verbose_loggers import (
    DummyVerboseLogger,
    SlackVerboseLogger,
    StorageVerboseLogger,
)


__all__ = [
    "DummyVerboseLogger",
    "SlackVerboseLogger",
    "StorageVerboseLogger",
]
