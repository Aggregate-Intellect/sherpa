"""Error handling module for Sherpa AI.

This module provides error handling functionality for the Sherpa AI system.
It exports the AgentErrorHandler class which handles various types of errors
that may occur during agent execution.

Example:
    >>> from sherpa_ai.error_handling import AgentErrorHandler
    >>> handler = AgentErrorHandler()
    >>> result = handler.run_with_error_handling(my_function, arg1="value1")
    >>> print(result)
    'Success' or error message if an error occurred
"""

from sherpa_ai.error_handling.agent_error_handler import AgentErrorHandler


__all__ = ["AgentErrorHandler"]
