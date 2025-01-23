import json
import re

import pytest
from langchain_community.chat_models import ChatOpenAI
from langchain_core.language_models import BaseLanguageModel, FakeListLLM
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from sherpa_ai.models.chat_model_with_logging import ChatModelWithLogging
from sherpa_ai.test_utils.loggers import get_new_logger


def get_fake_llm(filename, is_chat=False) -> FakeListLLM:
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
    logger = get_new_logger(filename)
    llm = ChatModelWithLogging(
        llm=ChatOpenAI(model_name=model_name, temperature=temperature), logger=logger
    )
    return llm


def format_cache_name(filename: str, method_name: str) -> str:
    filename = re.split("\\\\|/", filename)[-1].removesuffix(".py")
    return f"{filename}_{method_name}.jsonl"


@pytest.fixture
def get_llm(external_api: bool):
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
