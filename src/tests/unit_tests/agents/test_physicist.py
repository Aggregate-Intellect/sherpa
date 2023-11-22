import sys

import pytest
from loguru import logger

from sherpa_ai.agents import Physicist
from sherpa_ai.events import EventType
from sherpa_ai.memory import SharedMemory
from tests.fixtures.llms import get_llm


@pytest.fixture
def config_logger():
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")


@pytest.mark.external_api
def test_physicist_successful(config_logger, get_llm):
    llm = get_llm(__file__, test_physicist_successful.__name__)

    shared_memory = SharedMemory(
        objective="Develop an deep Learning-Based approach for estimating the maximum wind speed of a tropical cyclone using satellite imagery",  # noqa E501
        agent_pool=None,
    )
    physicist = Physicist(llm=llm, shared_memory=shared_memory)

    shared_memory.add(
        EventType.task,
        "Planner",
        "Conduct in-depth research to understand the meteorological aspects of tropical cyclones. Focus on understanding how specific features visible in satellite imagery, such as cloud patterns, temperature gradients, and precipitation patterns, can be related to the cyclone's maximum wind speed.",  # noqa E501
    )

    physicist.run()

    results = shared_memory.get_by_type(EventType.result)
    assert len(results) == 1
    logger.debug(results[0].content)
