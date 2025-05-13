"""Language model test utilities for Sherpa AI.

This module provides utilities for testing with both fake and real language
models. It includes functions for loading cached responses, creating test
loggers, and managing model configurations for testing purposes.
"""

import json
import re

import pytest
from langchain_community.chat_models import ChatOpenAI
from langchain_core.language_models import BaseLanguageModel, FakeListLLM
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from sherpa_ai.models.chat_model_with_logging import ChatModelWithLogging
from sherpa_ai.test_utils.loggers import get_new_logger


def get_fake_llm(filename, is_chat=False) -> FakeListLLM:
    """Create a fake language model using cached responses.

    This function loads pre-recorded responses from a file and creates a
    fake language model that returns these responses in sequence.

    Args:
        filename (str): Path to the file containing cached responses.
        is_chat (bool): Whether to create a chat model or completion model.

    Returns:
        FakeListLLM: A fake language model that returns cached responses.

    Example:
        >>> llm = get_fake_llm("responses.jsonl", is_chat=True)
        >>> response = llm.predict("Hello")
        >>> print(response)  # Returns first cached response
        'Hi there!'
    """
    responses = []
    with open(filename) as f:
        for line in f:
            responses.append(json.loads(line))
    # restore new line characters
    responses = [response["output"].replace("\\n", "\n") for response in responses]

    if not is_chat:
        return FakeListLLM(responses=responses)
    else:
        return FakeListChatModel(responses=responses)


def get_real_llm(
    filename: str, model_name: str = "gpt-4o-mini", temperature: int = 0
) -> ChatModelWithLogging:
    """Create a real language model with logging capabilities.

    This function creates a ChatOpenAI model wrapped with logging functionality
    that records all interactions to a file.

    Args:
        filename (str): Path to the file where logs will be written.
        model_name (str): Name of the OpenAI model to use.
        temperature (int): Sampling temperature for the model.

    Returns:
        ChatModelWithLogging: A language model with logging capabilities.

    Example:
        >>> llm = get_real_llm("chat.log", model_name="gpt-3.5-turbo")
        >>> response = llm.predict("What is Python?")
        >>> # Response is logged to chat.log
    """
    logger = get_new_logger(filename)
    llm = ChatModelWithLogging(
        llm=ChatOpenAI(model_name=model_name, temperature=temperature), logger=logger
    )
    return llm


def format_cache_name(filename: str, method_name: str) -> str:
    """Format a cache filename from test file and method names.

    This function creates a standardized cache filename by extracting the
    base name of the test file and combining it with the method name.

    Args:
        filename (str): Full path to the test file.
        method_name (str): Name of the test method.

    Returns:
        str: Formatted cache filename (e.g., "test_chat_basic.jsonl").

    Example:
        >>> name = format_cache_name("/tests/test_chat.py", "test_basic")
        >>> print(name)
        'test_chat_test_basic.jsonl'
    """
    filename = re.split("\\\\|/", filename)[-1].removesuffix(".py")
    return f"{filename}_{method_name}.jsonl"


@pytest.fixture
def get_llm(external_api: bool):
    """Pytest fixture for getting appropriate language models in tests.

    This fixture provides a function that returns either a real or fake
    language model based on the test configuration.

    Args:
        external_api (bool): Whether to use real external API calls.

    Returns:
        Callable: Function that creates language models for testing.

    Example:
        >>> def test_chat(get_llm):
        ...     llm = get_llm(__file__, "test_chat")
        ...     response = llm.predict("Hello")
        ...     assert response == "Hi!"
    """
    if external_api:
        # initialize the configuration loading
        import sherpa_ai.config  # noqa: F401

    def get(
        filename: str,
        method_name: str,
        folder: str = "data",
        is_chat: bool = False,
        **kwargs,
    ) -> BaseLanguageModel:
        """Get a language model for testing.

        Args:
            filename (str): Path to the test file.
            method_name (str): Name of the test method.
            folder (str): Folder containing test data.
            is_chat (bool): Whether to create a chat model.
            **kwargs: Additional arguments for real models.

        Returns:
            BaseLanguageModel: A language model for testing.
        """
        path = re.split("(\\\\|/)tests", filename)[0]
        folder = f"{path}/tests/{folder}"
        print(folder)
        filename = format_cache_name(filename, method_name)
        filename = f"{folder}/{filename}"
        if external_api:
            return get_real_llm(filename, **kwargs)
        else:
            return get_fake_llm(filename, is_chat)

    return get
