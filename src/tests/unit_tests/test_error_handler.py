import pytest
from functools import partial
from unittest.mock import MagicMock
from loguru import logger
from sherpa_ai.error_handling import AgentErrorHandler
from openai import (
    APIError,
    APIConnectionError,
    RateLimitError,
    AuthenticationError,
    APITimeoutError,
    BadRequestError,
)


class DummyLogger:
    def __init__(self):
        self.logs = []

    def log(self, message: str):
        self.logs.append(message)


def dummy_agent_action(exception: BaseException, question: str) -> str:
    if exception:
        raise exception
    return "dummy response"


class DummyError(Exception):
    pass


@pytest.fixture
def dummy_log():
    return DummyLogger()


@pytest.fixture
def configure_logger(dummy_log):
    logger.remove()
    logger.add(dummy_log.log)


def test_handling_predefined_errors_succeeds(configure_logger, dummy_log):
    error_handler = AgentErrorHandler()
    count = 0

    # Predefined error mapping (including OpenAI errors)
    error_cases = [
        (
            APIError("API Error", request=MagicMock(), body={}),
            "OpenAI API returned an API Error",
        ),
        (APIConnectionError(request=MagicMock()), "Failed to connect to OpenAI API"),
        (
            RateLimitError("Rate Limit Exceeded", response=MagicMock(), body={}),
            "OpenAI API request exceeded rate limit",
        ),
        (
            AuthenticationError("Authentication Failed", response=MagicMock(), body={}),
            "OpenAI API failed authentication or incorrect token",
        ),
        (APITimeoutError("Request Timeout"), "OpenAI API Timeout error"),
        (
            BadRequestError("Bad Request", response=MagicMock(), body={}),
            "OpenAI API invalid request error",
        ),
    ]

    for error, expected_message in error_cases:
        # Using partial to inject the error into dummy_agent_action
        action = partial(dummy_agent_action, exception=error)
        response = error_handler.run_with_error_handling(
            action, question="dummy question"
        )
        count += 1

        # Assert the response matches the expected error message
        assert response == expected_message
        assert len(dummy_log.logs) == count
        assert error.__class__.__name__ in str(dummy_log.logs[-1])


def test_handling_undefined_errors_succeeds(configure_logger, dummy_log):
    error_handler = AgentErrorHandler()
    action = partial(dummy_agent_action, exception=DummyError("Error happened"))
    response = error_handler.run_with_error_handling(action, question="dummy question")

    # Assert the response matches the default response for unknown errors
    assert response == error_handler.default_response
    assert len(dummy_log.logs) == 1
    assert "DummyError" in str(dummy_log.logs[0])
