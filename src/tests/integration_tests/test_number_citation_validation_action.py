from unittest.mock import patch

import pytest
from loguru import logger

from sherpa_ai.actions.number_validation import NumberValidationAction
import sherpa_ai.config as cfg
from sherpa_ai.agents import QAAgent
from sherpa_ai.events import EventType
from sherpa_ai.memory import SharedMemory
from sherpa_ai.memory.belief import Belief
from sherpa_ai.models.sherpa_base_chat_model import SherpaChatOpenAI
from sherpa_ai.output_parsers.number_validation import NumberValidation
from sherpa_ai.test_utils.llms import get_llm
from sherpa_ai.tools import SearchTool
from sherpa_ai.utils import combined_number_extractor


@pytest.mark.parametrize(
    " objective, input_data, expected_numbers",
    [
        (
            "What are the numbers in this text?",
            [
                {
                    "Document": "One Thousand Two Hundred Thirty-Four feet are also  567 and there are 56.45 others 123,345",
                    "Source": "https://www.sabioholding.com/press-releases/sabio-delivers-11-q2-2023-revenue-growth-led-by-57-increase-in-connected-tv-ott-sales",
                }
            ],
            ["1234", "567", "56.45", "123345"],
        ),
    ],
)
def test_number_citation_succeeds_in_qa(
    get_llm, input_data, expected_numbers, objective  # noqa: F811
):
    llm = get_llm(__file__, test_number_citation_succeeds_in_qa.__name__)
    data = input_data
    belief = Belief()
    shared_memory = SharedMemory(
        objective=objective,
        agent_pool=None,
    )
    number_validation = NumberValidationAction(belief=belief)
    with patch.object(SearchTool, "_run", return_value=data):
        task_agent = QAAgent(
            llm=llm,
            shared_memory=shared_memory,
            num_runs=1,
            actions=[number_validation],
            validation_steps=3,
            belief=belief,
        )

        shared_memory.add(
            EventType.task,
            "Planner",
            objective,
        )

        task_agent.run()

        results = shared_memory.get_by_type(EventType.result)
        logger.info(results[0].content)
        validation_exist = False
        for event in belief.internal_events:
            if "ValidationResult" in str(event):
                validation_exist = True
        assert validation_exist
