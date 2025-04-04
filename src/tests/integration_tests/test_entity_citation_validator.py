from unittest.mock import patch

import pytest
from loguru import logger
from nltk.metrics import jaccard_distance

import sherpa_ai.config as cfg  # noqa: F401
from sherpa_ai.agents.qa_agent import QAAgent
from sherpa_ai.memory import SharedMemory
from sherpa_ai.output_parsers.entity_validation import EntityValidation
from sherpa_ai.test_utils.llms import get_llm  # noqa: F401
from sherpa_ai.tools import SearchTool
from sherpa_ai.utils import extract_entities


@pytest.mark.parametrize(
    "test_id ,objective , input_data, expected_entities",
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
            ["Ethiopian", "Ethiopian Calendar Association", "kenya"],
        ),
        (
            1,
            "Tell me a fact about Star Trek: The Next Generation?",
            [
                {
                    "Document": "Star Trek is a 2009 movice. In it, the United Federation of Planets, a coalition of various planetary governments working for peace and cooperation. This document outlines the principles and regulations governing member worlds and their interactions. ",
                    "Source": "https://www.starTrek.com",
                }
            ],
            ["Star Trek", "the United Federation of Planets"],
        ),
    ],
)
def test_entity_citation_succeeds_in_qa(
    get_llm, test_id, objective, input_data, expected_entities  # noqa: F811
):
    llm = get_llm(
        __file__, test_entity_citation_succeeds_in_qa.__name__ + f"_{str(test_id)}"
    )

    shared_memory = SharedMemory(
        objective=objective,
        agent_pool=None,
    )

    entity_validation = EntityValidation()
    with patch.object(SearchTool, "_run", return_value=input_data):
        task_agent = QAAgent(
            llm=llm,
            shared_memory=shared_memory,
            num_runs=3,
            validations=[entity_validation],
            validation_steps=3,
        )

        shared_memory.add(
            "task",
            "Planner",
            content=objective,
        )

        task_agent.run()

        results = shared_memory.get_by_type("result")
        logger.info(results[0].content)
        result_entities = [s.lower() for s in extract_entities(results[0].content)]
        expected_entities = [s.lower() for s in expected_entities]
        logger.error(result_entities)
        logger.error(expected_entities)
        for entity in expected_entities:
            set_a = set(entity.split())  # Convert each string in a to a set of words
            match_found = any(
                1 - jaccard_distance(set_a, result_entity.split()) >= 0.7
                for result_entity in result_entities
            )

            if match_found or entity in results[0].content.lower():
                pass
            else:
                assert False, entity + " was not found in resource"
        assert True
