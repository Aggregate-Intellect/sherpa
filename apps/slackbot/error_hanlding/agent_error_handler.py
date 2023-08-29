from typing import Callable, Dict, List, Tuple

import openai
from loguru import logger


class AgentErrorHandler:
    say: Callable[[str], None]
    thread_ts: str
    error_map: Dict[BaseException, str]

    def __init__(self):
        self.error_map = {
            openai.error.APIError: "OpenAI API returned an API Error",
            openai.error.APIConnectionError: "Failed to connect to OpenAI API",
            openai.error.RateLimitError: "OpenAI API request exceeded rate limit",
            openai.error.AuthenticationError: (
                "OpenAI API failed authentication or incorrect token"
            ),
            openai.error.Timeout: "OpenAI API Timeout error",
            openai.error.ServiceUnavailableError: "OpenAI API Service unavailable",
            openai.error.InvalidRequestError: "OpenAI API invalid request error",
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
        """
        try:
            return executable(**kwargs)
        except Exception as e:
            logger.exception(e)
            error_message = self.error_map.get(type(e), self.default_response)
            return error_message
