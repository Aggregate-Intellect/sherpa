import sys

import pytest
from loguru import logger

from sherpa_ai.agents import MLEngineer
from sherpa_ai.events import EventType
from sherpa_ai.memory import SharedMemory
from sherpa_ai.test_utils.llms import get_llm
from sherpa_ai.test_utils.loggers import config_logger_level


@pytest.mark.external_api
def test_ml_engineer_succeeds(config_logger_level, get_llm):  # noqa: F811
    # config_logger_level()
    llm = get_llm(__file__, test_ml_engineer_succeeds.__name__)

    shared_memory = SharedMemory(
        objective="Develop an deep Learning-Based approach for estimating the maximum wind speed of a tropical cyclone using satellite imagery",  # noqa E501
        agent_pool=None,
    )
    ml_engineer = MLEngineer(llm=llm, shared_memory=shared_memory)

    shared_memory.add(
        EventType.task,
        "Planner",
        "Develop a machine learning algorithm based on the refined theoretical model. Specifically, use a Neural Network algorithm with parameters set to optimally process the identified variables. The objective is to estimate maximum wind speed of a tropical cyclone from satellite imagery.",  # noqa E501
    )

    ml_engineer.run()

    results = shared_memory.get_by_type(EventType.result)
    assert len(results) == 1
    logger.debug(results[0].content)
