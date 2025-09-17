"""Verbose logging package for Sherpa AI.

This package provides various logging implementations for verbose output
in different contexts. It includes loggers for Slack messaging, file logging,
testing, and no-op scenarios.

Example:
    >>> from sherpa_ai.verbose_loggers import StorageVerboseLogger
    >>> logger = StorageVerboseLogger()
    >>> logger.log("Test message")
    >>> print(logger.storage)
    ['Test message']
    
    >>> from sherpa_ai.verbose_loggers import FileVerboseLogger
    >>> file_logger = FileVerboseLogger("usage.log")
    >>> file_logger.log("Usage data logged to file")
"""

from sherpa_ai.verbose_loggers.verbose_loggers import (
    DummyVerboseLogger,
    FileVerboseLogger,
    SlackVerboseLogger,
    StorageVerboseLogger,
)


__all__ = [
    "DummyVerboseLogger",
    "FileVerboseLogger",
    "SlackVerboseLogger",
    "StorageVerboseLogger",
]
