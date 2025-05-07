"""Base verbose logger module for Sherpa AI.

This module provides the abstract base class for verbose loggers, defining
the interface that all verbose loggers must implement.
"""

from abc import ABC, abstractmethod


class BaseVerboseLogger(ABC):
    """Abstract base class for verbose loggers.

    This class defines the interface for verbose loggers in the system.
    All concrete logger implementations must inherit from this class and
    implement the log method.

    Example:
        >>> class MyLogger(BaseVerboseLogger):
        ...     def log(self, message: str):
        ...         print(f"LOG: {message}")
        >>> logger = MyLogger()
        >>> logger.log("Hello")
        'LOG: Hello'
    """

    @abstractmethod
    def log(self, message: str):
        """Log a message.

        Args:
            message (str): The message to log.
        """
        pass
