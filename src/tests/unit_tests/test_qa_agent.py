import sys

import pytest
from langchain.chat_models import ChatOpenAI
from loguru import logger

import sherpa_ai.config
from sherpa_ai.agents import QAAgent
from sherpa_ai.events import EventType
from sherpa_ai.memory import SharedMemory


@pytest.fixture
def config_logger():
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")


def test_task_agent(config_logger):
    llm = ChatOpenAI(model_name='gpt-3.5-turbo')

    shared_memory = SharedMemory(
        objective="What is AutoGPT?",
        agent_pool=None,
    )

    task_agent = QAAgent(
        llm=llm,
        shared_memory=shared_memory,
    )

    shared_memory.add(
        EventType.task,
        "Planner",
        "What is AutoGPT?",
    )

    task_agent.run()

    results = shared_memory.get_by_type(EventType.result)
    assert len(results) == 1
    logger.debug(results[0].content)
