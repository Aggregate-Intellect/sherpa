from unittest.mock import patch

import pytest
from loguru import logger
from nltk.metrics import jaccard_distance

import sherpa_ai.config as cfg
from sherpa_ai.agents.qa_agent import QAAgent
from sherpa_ai.events import EventType
from sherpa_ai.memory import SharedMemory
from sherpa_ai.models.sherpa_base_chat_model import SherpaChatOpenAI
from sherpa_ai.output_parsers.entity_validation import EntityValidation

# from sherpa_ai.test_utils.llms import get_llm
from sherpa_ai.tools import SearchTool
from sherpa_ai.utils import extract_entities


@pytest.mark.parametrize(
    "objective , input_data, expected_entities",
    [
        (
            "what is unique about Ethiopia calendar?  based on USA calendar assosation. ",
            (
                """
                According to Ethiopian calendar Assosation (ECA) , Ethiopia has thirteen months. Canada and Kenya also mentioned this. also recognized by World Calendar Assosation (WCA) """,
                [
                    {
                        "Document": "Ethiopian calendar",
                        "Source": "https://www.sabioholding.com/press-releases/sabio-delivers-11-q2-2023-revenue-growth-led-by-57-increase-in-connected-tv-ott-sales",
                    }
                ],
            ),
            ["Ethiopian", "Ethiopian Calendar Association", "kenya"],
        ),
        (
            "Tell me a fact about Star Trek: The Next Generation?",
            (
                """Fact: In Star Trek: The Next Generation (STNG), the United Federation of Planets, a coalition of various planetary governments working for peace and cooperation, establishes a set of interstellar laws known as the "Federation Charter." This document outlines the principles and regulations governing member worlds and their interactions. """,
                [
                    {
                        "Document": "Star Trek: The Next Generation",
                        "Source": "https://www.starTrek.com",
                    }
                ],
            ),
            ["STNG", "Star Trek", "the United Federation of Planets"],
        ),
    ],
)
def test_entity_citation_succeeds_in_qa(input_data, expected_entities, objective):
    # noqa: F811
    # llm = get_llm(__file__, test_number_citation_succeeds_in_qa.__name__)
    llm = SherpaChatOpenAI(
        openai_api_key=cfg.OPENAI_API_KEY,
        temperature=0,
    )

    data = input_data[0]

    shared_memory = SharedMemory(
        objective=objective,
        agent_pool=None,
    )

    entity_validation = EntityValidation()
    with patch.object(SearchTool, "_run", return_value=data):
        task_agent = QAAgent(
            llm=llm,
            shared_memory=shared_memory,
            num_runs=3,
            validations=[entity_validation],
            validation_steps=3,
        )

        shared_memory.add(
            EventType.task,
            "Planner",
            objective,
        )

        task_agent.run()

        results = shared_memory.get_by_type(EventType.result)
        logger.error(results[0].content)
        result_entities = [s.lower() for s in extract_entities(results[0].content)]
        expected_entities = [s.lower() for s in expected_entities]
        for entitity in expected_entities:
            set_a = set(entitity.split())  # Convert each string in a to a set of words
            match_found = any(
                1 - jaccard_distance(set_a, result_entity.split()) >= 0.7
                for result_entity in result_entities
            )

            if match_found:
                pass
            else:
                assert False, entitity + " was not found in resource"
        assert True
