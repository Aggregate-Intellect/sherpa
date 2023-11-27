import sys

import pytest
from loguru import logger

from sherpa_ai.agents import Physicist
from sherpa_ai.events import EventType
from sherpa_ai.memory import SharedMemory
from tests.fixtures.llms import get_llm
from tests.fixtures.loggers import config_logger_level


@pytest.mark.external_api
def test_physicist_succeeds(config_logger_level, get_llm):  # noqa: F811
    # config_logger_level()
    llm = get_llm(__file__, test_physicist_succeeds.__name__)

    shared_memory = SharedMemory(
        objective="Develop a deep learning-Based approach for estimating the maximum wind speed of a tropical cyclone using satellite imagery",  # noqa E501
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
