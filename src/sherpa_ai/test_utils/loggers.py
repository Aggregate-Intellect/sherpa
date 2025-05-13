"""Logger test utilities for Sherpa AI.

This module provides utilities for creating and configuring loggers during
testing. It includes functions for creating isolated loggers and managing
logging levels without affecting the global logger configuration.
"""

import copy
import sys
from typing import Callable

import pytest
from loguru import logger


def get_new_logger(filename, level="INFO") -> Callable[[str], type(logger)]:
    """Create a new isolated logger instance.

    This function creates a new logger that writes to a specified file while
    keeping the global logger configuration unchanged. It's particularly
    useful for testing scenarios where you want to capture logs without
    affecting other parts of the system.

    Reference: https://github.com/Delgan/loguru/issues/487

    Args:
        filename (str): Path to the file where logs will be written.
        level (str): Logging level (e.g., "INFO", "DEBUG").

    Returns:
        Callable[[str], type(logger)]: A new logger instance.

    Example:
        >>> test_logger = get_new_logger("test.log", level="DEBUG")
        >>> test_logger.info("Test message")  # Written to test.log
        >>> logger.info("Global message")     # Uses global configuration
    """
    logger.remove()
    child_logger = copy.deepcopy(logger)

    # add handler back
    logger.add(sys.stderr)

    child_logger.add(filename, level=level, format="{message}", mode="w")

    return child_logger


@pytest.fixture
def config_logger_level() -> Callable[[str], None]:
    """Pytest fixture for configuring logger level during tests.

    This fixture provides a function that temporarily changes the global
    logger's level for the duration of a test.

    Returns:
        Callable[[str], None]: Function to set logger level.

    Example:
        >>> def test_logging(config_logger_level):
        ...     config_logger_level("DEBUG")
        ...     logger.debug("Debug message")  # Now visible
        ...     config_logger_level("INFO")
        ...     logger.debug("Debug message")  # Now hidden
    """
    def get(level="DEBUG"):
        """Set the global logger's level.

        Args:
            level (str): Logging level to set (default: "DEBUG").
        """
        logger.remove()
        logger.add(sys.stderr, level=level)

    return get
