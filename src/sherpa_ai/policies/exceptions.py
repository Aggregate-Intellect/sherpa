"""Policy exception classes for Sherpa AI.

This module provides exception classes for handling policy-related errors.
It defines the SherpaPolicyException class which captures detailed error
information including stack traces.
"""

import traceback


class SherpaPolicyException(Exception):
    """Exception raised for policy-related errors.

    This class extends the base Exception class to add stack trace capture
    and custom message handling for policy errors.

    Attributes:
        message (str): Detailed error message.
        stacktrace (list[str]): Stack trace at the point of error.

    Example:
        >>> try:
        ...     raise SherpaPolicyException("Invalid action")
        ... except SherpaPolicyException as e:
        ...     print(e.message)
        ...     print(len(e.stacktrace) > 0)  # Has stack trace
        'Invalid action'
        True
    """

    def __init__(self, message):
        """Initialize a new policy exception.

        Args:
            message (str): Error message describing what went wrong.

        Example:
            >>> e = SherpaPolicyException("Action failed")
            >>> print(e.message)
            'Action failed'
        """
        super().__init__(message)
        self.message = message
        self.stacktrace = traceback.format_stack()
