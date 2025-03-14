import json
import re

import pytest 
from langchain_core.language_models import BaseLanguageModel 
from langchain_community.chat_models import ChatOpenAI 
from langchain_core.language_models import FakeListLLM 

from sherpa_ai.models.chat_model_with_logging import ChatModelWithLogging
from sherpa_ai.test_utils.loggers import get_new_logger


def get_fake_llm(filename) -> FakeListLLM:
    responses = []
    with open(filename) as f:
        for line in f:
            responses.append(json.loads(line))
    # restore new line characters
    responses = [response["output"].replace(
        "\\n", "\n") for response in responses]
    return FakeListLLM(responses=responses)


def get_real_llm(
    filename: str, model_name: str = "gpt-3.5-turbo", temperature: int = 0
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
        import sherpa_ai.config

    def get(
        filename: str, method_name: str, folder: str = "data", **kwargs
    ) -> BaseLanguageModel:
        path = re.split("(\\\\|/)tests", filename)[0]
        folder = f"{path}/tests/{folder}"
        print(folder)
        filename = format_cache_name(filename, method_name)
        filename = f"{folder}/{filename}"
        if external_api:
            return get_real_llm(filename, **kwargs)
        else:
            return get_fake_llm(filename)

    return get
