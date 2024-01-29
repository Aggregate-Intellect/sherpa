import sys

import pytest
from loguru import logger

from sherpa_ai.agents import QAAgent
from sherpa_ai.events import EventType
from sherpa_ai.memory import SharedMemory
from sherpa_ai.test_utils.llms import get_llm


def test_task_agent_succeeds(get_llm):  # noqa: F811
    llm = get_llm(__file__, test_task_agent_succeeds.__name__)

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
