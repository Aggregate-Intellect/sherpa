import json

import pytest
from langchain.chat_models import ChatOpenAI
from langchain.llms import FakeListLLM


@pytest.fixture
def get_fake_llm():
    def get(filename):
        responses = []
        with open(filename) as f:
            for line in f:
                responses.append(json.loads(line))

        responses = [response["output"].replace("\\n", "\n") for response in responses]

        return FakeListLLM(responses=responses)

    return get


@pytest.fixture
def get_real_llm():
    def get(model_name="gpt-3.5-turbo"):
        return ChatOpenAI(model_name=model_name)

    return get
