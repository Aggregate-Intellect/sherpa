import sys

import pytest
from langchain.chat_models import ChatOpenAI
from loguru import logger

import sherpa_ai.config
from sherpa_ai.agents import Physicist
from sherpa_ai.events import EventType
from sherpa_ai.memory import SharedMemory


@pytest.fixture
def config_logger():
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")


def test_physicist(config_logger):
    llm = ChatOpenAI(model_name='gpt-4')

    shared_memory = SharedMemory(
        objective="Develop an deep Learning-Based approach for estimating the maximum wind speed of a tropical cyclone using satellite imagery",
        agent_pool=None,
    )
    physicist = Physicist(llm=llm, shared_memory=shared_memory)

    shared_memory.add(
        EventType.task,
        "Planner",
        "Conduct in-depth research to understand the meteorological aspects of tropical cyclones. Focus on understanding how specific features visible in satellite imagery, such as cloud patterns, temperature gradients, and precipitation patterns, can be related to the cyclone's maximum wind speed.",
    )

    physicist.run()

    results = shared_memory.get_by_type(EventType.result)
    assert len(results) == 1
    logger.debug(results[0].content)
