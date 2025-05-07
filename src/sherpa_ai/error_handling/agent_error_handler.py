from typing import Callable, Dict, List, Tuple

import openai
from loguru import logger


class AgentErrorHandler:
    """
    Handles errors that occur during agent execution.

    Attributes:
        say (Callable[[str], None]): The function to call to send a message.
        thread_ts (str): The thread timestamp of the message.
        error_map (Dict[BaseException, str]): The map of errors to messages.
        default_response (str): The default response to send if an error occurs.

    Example:
        >>> handler = AgentErrorHandler()
        >>> handler.run_with_error_handling(my_function, x=5)
        '10'
        >>> handler.run_with_error_handling(my_function, x="invalid")
        'An unexpected error occurred. Please try again.'
    """
    say: Callable[[str], None]
    thread_ts: str
    error_map: Dict[BaseException, str]

    def __init__(self):
        self.error_map = {
            openai.APIError: "OpenAI API returned an API Error",
            openai.APIConnectionError: "Failed to connect to OpenAI API",
            openai.RateLimitError: "OpenAI API request exceeded rate limit",
            openai.AuthenticationError: (
                "OpenAI API failed authentication or incorrect token"
            ),
            openai.APITimeoutError: "OpenAI API Timeout error",
            openai.BadRequestError: "OpenAI API invalid request error",
        }
        self.default_response = (
            "Sorry, some error occurred. Please try again or contact the developer."
        )

    def run_with_error_handling(self, executable: Callable[[str], str], **kwargs):
        """
        Run the executable with error handling. If an error occurs,
        return the error message.

        Args:
            executable (Callable[[str, List[Dict]], Tuple[str, List[str]]]): The
                executable to run with input (question, previous_messages) and
                returns a tuple of (response, log).
            **kwargs: The input arguments for the executable.

        Returns:
            str: The result of the function execution or an error message if an exception occurs.

        Example:
            >>> handler = AgentErrorHandler()
            >>> result = handler.run_with_error_handling(my_function, x=5)
            >>> print(result)
            '10'
            >>> result = handler.run_with_error_handling(my_function, x="invalid")
            >>> print(result)
            'An unexpected error occurred. Please try again.'
        """
        try:
            return executable(**kwargs)
        except Exception as e:
            logger.exception(e)
            error_message = self.error_map.get(type(e), self.default_response)
            return error_message
