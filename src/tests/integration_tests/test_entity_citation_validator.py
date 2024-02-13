import pytest
from loguru import logger

from sherpa_ai.agents import QAAgent
from sherpa_ai.events import EventType
from sherpa_ai.memory import SharedMemory
from sherpa_ai.models.sherpa_base_chat_model import SherpaChatOpenAI
from sherpa_ai.test_utils.llms import get_llm
from sherpa_ai.tools import SearchTool
import sherpa_ai.config as cfg
from unittest.mock import patch
from sherpa_ai.utils import extract_numbers_from_text


@pytest.mark.parametrize(
    "objective , input_data, expected_numbers",
    [
        (
            "what is unique about Ethiopian callender? and Please provide the answer in numerical form. based on USA callendar assosation.",
            (
                """
                Ethiopia has callender has thirteen months.""",
                [
                    {
                        "Document": "soccer",
                        "Source": "https://www.sabioholding.com/press-releases/sabio-delivers-11-q2-2023-revenue-growth-led-by-57-increase-in-connected-tv-ott-sales",
                    }
                ],
            ),
            [],
        ),
    ],
)
def test_entity_citation_succeeds_in_qa(
    get_llm, input_data, expected_numbers, objective
):  # noqa: F811
    # llm = get_llm(__file__, test_number_citation_succeeds_in_qa.__name__)
    llm = SherpaChatOpenAI(
        openai_api_key=cfg.OPENAI_API_KEY,
        temperature=cfg.TEMPRATURE,
    )

    data = input_data[0]

    shared_memory = SharedMemory(
        objective=objective,
        agent_pool=None,
    )
    with patch.object(SearchTool, "_run", return_value=data):
        task_agent = QAAgent(llm=llm, shared_memory=shared_memory, require_meta=False)

        shared_memory.add(
            EventType.task,
            "Planner",
            objective,
        )

        task_agent.run()

        results = shared_memory.get_by_type(EventType.result)
        data_numbers = expected_numbers
        logger.error(results[0].content)
        for number in extract_numbers_from_text(results[0].content):
            if number in data_numbers or len(data_numbers) == 0:
                pass
            else:
                assert False, number + " was not found in resource"

        assert True
