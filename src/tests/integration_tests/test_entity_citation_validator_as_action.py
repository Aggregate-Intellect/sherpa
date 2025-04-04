from unittest.mock import patch

import pytest
from loguru import logger

import sherpa_ai.config as cfg
from sherpa_ai.actions.entity_validation import EntityValidationAction
from sherpa_ai.actions.google_search import GoogleSearch
from sherpa_ai.agents.qa_agent import QAAgent
from sherpa_ai.memory import SharedMemory
from sherpa_ai.memory.belief import Belief
from sherpa_ai.test_utils.llms import get_llm
from sherpa_ai.tools import SearchTool


@pytest.mark.parametrize(
    "test_id ,objective , input_data",
    [
        (
            0,
            "what is unique about Ethiopia calendar?  based on USA calendar assosation. ",
            [
                {
                    "Document": "According to Ethiopian calendar Assosation (ECA) , Ethiopia has thirteen months. Canada and Kenya also mentioned this. also recognized by World Calendar Assosation (WCA)",
                    "Source": "https://www.sabioholding.com/press-releases/sabio-delivers-11-q2-2023-revenue-growth-led-by-57-increase-in-connected-tv-ott-sales",
                }
            ],
        ),
    ],
)
def test_entity_citation_succeeds_in_qa(
    get_llm, test_id, objective, input_data  # noqa: F811
):
    llm = get_llm(
        __file__, test_entity_citation_succeeds_in_qa.__name__ + f"_{str(test_id)}"
    )

    belief = Belief()
    shared_memory = SharedMemory(
        objective=objective,
        agent_pool=None,
    )
    google_search = GoogleSearch(
        role_description="Planner",
        task="What is AutoGPT?",
        llm=llm,
    )

    entity_validation_action = EntityValidationAction(llm=llm, belief=belief)

    with patch.object(SearchTool, "_run", return_value=input_data):
        task_agent = QAAgent(
            llm=llm,
            shared_memory=shared_memory,
            num_runs=3,
            actions=[google_search, entity_validation_action],
            validation_steps=3,
            belief=belief,
        )

        shared_memory.add(
            "task",
            "Planner",
            content=objective,
        )

        task_agent.run()

        results = shared_memory.get_by_type("result")
        logger.info(results[0].content)
        validation_exist = False
        for event in belief.internal_events:
            if "ValidationResult" in str(event):
                validation_exist = True
        assert validation_exist
