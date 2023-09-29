import sys

import pytest
from langchain.chat_models import ChatOpenAI
from loguru import logger

import sherpa_ai.config
from sherpa_ai.agents import MLEngineer
from sherpa_ai.events import EventType
from sherpa_ai.memory import SharedMemory


@pytest.fixture
def config_logger():
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")


def test_physicist(config_logger):
    llm = ChatOpenAI(model_name="gpt-4")

    shared_memory = SharedMemory(
        objective="Develop an deep Learning-Based approach for estimating the maximum wind speed of a tropical cyclone using satellite imagery",
        agent_pool=None,
    )
    ml_engineer = MLEngineer(llm=llm, shared_memory=shared_memory)

    shared_memory.add(
        EventType.task,
        "Planner",
        "Develop a machine learning algorithm based on the refined theoretical model. Specifically, use a Neural Network algorithm with parameters set to optimally process the identified variables. The objective is to estimate maximum wind speed of a tropical cyclone from satellite imagery.",
    )

    ml_engineer.run()

    results = shared_memory.get_by_type(EventType.result)
    assert len(results) == 1
    logger.debug(results[0].content)
