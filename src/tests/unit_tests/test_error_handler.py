"""Unit testing the error handler"""
from functools import partial
from typing import Dict, List

import pytest
from loguru import logger

from sherpa_ai.error_handling import AgentErrorHandler


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


def test_handling_predefined_errors(configure_logger, dummy_log):
    error_handler = AgentErrorHandler()
    count = 0
    for error, error_message in error_handler.error_map.items():
        action = partial(dummy_agent_action, exception=error("Error happened", []))
        response = error_handler.run_with_error_handling(
            action,
            question="dummy question",
        )
        count += 1

        assert response == error_message
        assert len(dummy_log.logs) == count
        assert error.__name__ in str(dummy_log.logs[-1])


def test_handling_undefined_errors(configure_logger, dummy_log):
    error_handler = AgentErrorHandler()
    action = partial(dummy_agent_action, exception=DummyError("Error happened"))
    response = error_handler.run_with_error_handling(
        action,
        question="dummy question",
    )
    assert response == error_handler.default_response
    assert len(dummy_log.logs) == 1
    assert isinstance(dummy_log.logs[0], str)


def test_no_error(configure_logger, dummy_log):
    error_handler = AgentErrorHandler()
    action = partial(dummy_agent_action, exception=None)
    response = error_handler.run_with_error_handling(
        action,
        question="dummy question",
    )
    assert response == "dummy response"
    assert len(dummy_log.logs) == 0
