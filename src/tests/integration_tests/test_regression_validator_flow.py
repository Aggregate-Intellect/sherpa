from unittest.mock import patch

import pytest
from loguru import logger
from nltk.metrics import jaccard_distance

import sherpa_ai.config as cfg
from sherpa_ai.agents.qa_agent import QAAgent
from sherpa_ai.memory import SharedMemory
from sherpa_ai.models.sherpa_base_chat_model import SherpaChatOpenAI
from sherpa_ai.output_parsers.citation_validation import CitationValidation
from sherpa_ai.output_parsers.entity_validation import EntityValidation
from sherpa_ai.output_parsers.number_validation import NumberValidation
from sherpa_ai.test_utils.llms import get_llm
from sherpa_ai.tools import SearchTool
from sherpa_ai.utils import combined_number_extractor, extract_entities


@pytest.mark.parametrize(
    "test_id ,objective , input_data, expected_entities, expected_number",
    [
        (
            0,
            "what is unique about Ethiopia calendar?  based on USA calendar association. what is the number of months ",
            [
                {
                    "Document": "According to Ethiopian calendar Association (ECA) , Ethiopia has thirteen months. Canada and Kenya also mentioned this. also recognized by World Calendar Association (WCA) , Addis Ababa , AU , 34.5 , 9000 , Africa",
                    "Source": "https://www.sabioholding.com/press-releases/sabio-delivers-11-q2-2023-revenue-growth-led-by-57-increase-in-connected-tv-ott-sales",
                }
            ],
            ["Ethiopian", "Ethiopian Calendar Association", "kenya"],
            ["13"],
        ),
    ],
)
def test_regression_validator_flow(
    get_llm,  # noqa F811
    test_id,
    objective,
    input_data,
    expected_entities,
    expected_number,
):
    llm = get_llm(
        __file__, test_regression_validator_flow.__name__ + f"_{str(test_id)}"
    )
    data = input_data

    shared_memory = SharedMemory(
        objective=objective,
        agent_pool=None,
    )

    entity_validation = EntityValidation()
    number_validation = NumberValidation()
    number_validation_two = NumberValidation()
    citation_validation = CitationValidation()
    with patch.object(SearchTool, "_run", return_value=data):
        task_agent = QAAgent(
            llm=llm,
            shared_memory=shared_memory,
            num_runs=3,
            validations=[
                entity_validation,
                number_validation,
                number_validation_two,
                citation_validation,
            ],
            validation_steps=3,
            global_regen_max=14,
        )

        shared_memory.add(
            "task",
            "Planner",
            content=objective,
        )

        task_agent.run()

        results = shared_memory.get_by_type("result")
        logger.info(results[0].content)
        final_result = results[0].content

        if not entity_validation.get_failure_message() in final_result:
            result_entities = [s.lower() for s in extract_entities(results[0].content)]
            expected_entities = [s.lower() for s in expected_entities]
            for entity in expected_entities:
                set_a = set(
                    entity.split()
                )  # Convert each string in a to a set of words
                match_found = any(
                    1 - jaccard_distance(set_a, result_entity.split()) >= 0.7
                    for result_entity in result_entities
                )

                if not match_found:
                    assert False, entity + " was not found in resource"
        if not number_validation.get_failure_message() in final_result:
            for number in expected_number:
                if number not in combined_number_extractor(results[0].content):
                    assert False, number + " was not found in resource"
        assert True
