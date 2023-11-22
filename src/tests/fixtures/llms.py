import json
import re

import pytest
from langchain.base_language import BaseLanguageModel
from langchain.chat_models import ChatOpenAI
from langchain.llms import FakeListLLM

from sherpa_ai.models.sherpa_logger_chat_model import SherpaLoggerLLM
from tests.fixtures.loggers import get_logger


def get_fake_llm(filename) -> FakeListLLM:
    responses = []
    with open(filename) as f:
        for line in f:
            responses.append(json.loads(line))

    responses = [response["output"].replace("\\n", "\n") for response in responses]

    return FakeListLLM(responses=responses)


def get_real_llm(
    filename: str, model_name: str = "gpt-3.5-turbo", temperature: int = 0
) -> SherpaLoggerLLM:
    logger = get_logger(filename)
    llm = SherpaLoggerLLM(
        llm=ChatOpenAI(model_name=model_name, temperature=temperature), logger=logger
    )
    return llm


def format_cache_name(filename: str, method_name: str) -> str:
    filename = re.split("\\\\|/", filename)[-1].removesuffix(".py")
    return f"{filename}_{method_name}.jsonl"


@pytest.fixture
def get_llm(external_api: bool):
    if external_api:
        import sherpa_ai.config

    def get(
        filename: str, method_name: str, folder: str = "tests/data", **kwargs
    ) -> BaseLanguageModel:
        filename = format_cache_name(filename, method_name)
        filename = f"{folder}/{filename}"
        if external_api:
            return get_real_llm(filename, **kwargs)
        else:
            return get_fake_llm(filename)

    return get
