import os
from typing import Callable

from langchain.chat_models import ChatOpenAI
from langchain.llms import FakeListLLM
from loguru import logger

import sherpa_ai.config as cfg
from sherpa_ai.agents.agent_pool import AgentPool
from sherpa_ai.agents.physicist import Physicist
from sherpa_ai.agents.planner import Planner

# from sherpa_ai.agents.programmer import Programmer
from sherpa_ai.memory.shared_memory import SharedMemory
from sherpa_ai.models.sherpa_logger_chat_model import SherpaLoggerLLM
from tests.fixtures.llms import get_fake_llm, get_real_llm
from tests.fixtures.loggers import get_logger


def test_planner(
    get_logger: Callable[[str], type(logger)],  # noqa: F811 (redefinition of variable)
    get_fake_llm: Callable[[str], FakeListLLM],  # noqa: F811
    get_real_llm: Callable[[str], ChatOpenAI],  # noqa: F811
    external_api: bool,
):
    cache_name = "tests/data/test_planner_test_planner.json"
    if external_api:
        logger = get_logger(cache_name)
        llm = SherpaLoggerLLM(llm=get_real_llm(), logger=logger)
    else:
        llm = get_fake_llm(cache_name)

    physicist_description = (
        "The physicist agent answers questions or research about physics-related topics"
    )
    physicist = Physicist(
        name="Physicist",
        description=physicist_description,
        llm=llm,
    )

    agent_pool = AgentPool()
    agent_pool.add_agents([physicist])

    shared_memory = SharedMemory(
        objective="Share the information across different agents.",
        agent_pool=agent_pool,
    )

    planner = Planner(
        name="planner",
        agent_pool=agent_pool,
        shared_memory=shared_memory,
        llm=llm,
    )

    task = """We need to render a highly complex 3D image on the solar system. We can use any publicly avaliable
    resources to achieve this task."""  # noqa: E501

    p = planner.plan(task=task)
    assert len(p.steps) > 0
