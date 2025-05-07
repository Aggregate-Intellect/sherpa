"""Verbose logger implementations for Sherpa AI.

This module provides concrete implementations of verbose loggers for different
purposes, including Slack messaging, testing, and no-op logging.
"""

from typing import Callable, List

from sherpa_ai.verbose_loggers.base import BaseVerboseLogger


class SlackVerboseLogger(BaseVerboseLogger):
    """Verbose logger for Slack messaging.

    This logger sends messages to a Slack channel or thread using the Bolt
    framework's say utility function.

    Attributes:
        logger (Callable[[str], None]): Bolt's say function for sending messages.
        thread_ts (str): Timestamp of the Slack thread to post in.

    Example:
        >>> def say_func(msg, thread_ts):
        ...     print(f"Slack({thread_ts}): {msg}")
        >>> logger = SlackVerboseLogger(say_func, "1234567890")
        >>> logger.log("Hello Slack!")
        'Slack(1234567890): Hello Slack!'
    """

    # the say utility function from Bolt
    logger: Callable[[str], None]
    thread_ts: str

    def __init__(self, logger: Callable[[str], None], thread_ts: str):
        """Initialize the Slack logger.

        Args:
            logger (Callable[[str], None]): Bolt's say function.
            thread_ts (str): Slack thread timestamp.
        """
        self.logger = logger
        self.thread_ts = thread_ts

    def log(self, message: str):
        """Send a message to Slack.

        Args:
            message (str): Message to send to Slack.
        """
        self.logger(message, thread_ts=self.thread_ts)


class DummyVerboseLogger(BaseVerboseLogger):
    """No-op verbose logger.

    This logger discards all messages without processing them. It's useful
    when verbose logging is disabled but the logging interface is still needed.

    Example:
        >>> logger = DummyVerboseLogger()
        >>> logger.log("This message is ignored")  # Does nothing
    """

    def log(self, message: str):
        """Discard a message without processing.

        Args:
            message (str): Message to discard.
        """
        pass


class StorageVerboseLogger(BaseVerboseLogger):
    """In-memory storage verbose logger.

    This logger stores all messages in a list for later inspection. It's
    particularly useful for testing and debugging purposes.

    Attributes:
        storage (List[str]): List of stored messages.

    Example:
        >>> logger = StorageVerboseLogger()
        >>> logger.log("First message")
        >>> logger.log("Second message")
        >>> print(logger.storage)
        ['First message', 'Second message']
    """

    storage: List[str]

    def __init__(self):
        """Initialize the storage logger with an empty list."""
        self.storage = []

    def log(self, message: str):
        """Store a message in the internal list.

        Args:
            message (str): Message to store.
        """
        self.storage.append(message)
