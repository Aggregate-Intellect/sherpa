from unittest.mock import patch

import pytest
from loguru import logger

from sherpa_ai.actions.link_scraper import LinkScraperAction
from sherpa_ai.actions.google_search import GoogleSearch
import sherpa_ai.config as cfg
from sherpa_ai.agents.qa_agent import QAAgent
from sherpa_ai.events import EventType
from sherpa_ai.memory import SharedMemory
from sherpa_ai.memory.belief import Belief
from sherpa_ai.models.sherpa_base_chat_model import SherpaChatOpenAI
from sherpa_ai.test_utils.llms import get_llm
from sherpa_ai.tools import LinkScraperTool
from sherpa_ai.utils import extract_entities


@pytest.mark.parametrize(
    "test_id, objective, input_data",
    [
        (
            0,
            "what is unique about Ethiopia calendar? based on these links https://www.ethiopiancalendar.net/",
            {
                "Document": "The Ethiopia calendar is similar to the Coptic Egyptian calendar since both have 13 months, 12 of which have 30 days and an intercalary month at the end of the year called Pagume which means 'forgotten days' in Greek. This last month has five days or six days in a leap year.",
                "Source": "https://www.ethiopiancalendar.net/"
            },
        ),
        (
            1,
            "what is unique about Ethiopia calendar? based on this link https://en.wikipedia.org/wiki/Ethiopian_calendar",
            {
                "Document": "The Ethiopian calendar is a solar calendar that is derived from the Egyptian calendar, but with some differences. It has 13 months: 12 of 30 days each and an additional month at the end of the year with five or six days.",
                "Source": "https://en.wikipedia.org/wiki/Ethiopian_calendar"
            },
        )
    ],
)
def test_link_scraper_succeeds_in_qa(
    get_llm, test_id, objective, input_data,
):
    def mock_run(url):
        if url == "https://www.ethiopiancalendar.net/":
            return {
                "Document": "The Ethiopia calendar is similar to the Coptic Egyptian calendar since both have 13 months, 12 of which have 30 days and an intercalary month at the end of the year called Pagume which means 'forgotten days' in Greek. This last month has five days or six days in a leap year.",
                "Source": "https://www.ethiopiancalendar.net/"
            }
        elif url == "https://en.wikipedia.org/wiki/Ethiopian_calendar":
            return {
                "Document": "The Ethiopian calendar is a solar calendar that is derived from the Egyptian calendar, but with some differences. It has 13 months: 12 of 30 days each and an additional month at the end of the year with five or six days.",
                "Source": "https://en.wikipedia.org/wiki/Ethiopian_calendar"
            }
        else:
            return {
                "Document": "Unknown content",
                "Source": url
            }
    llm = get_llm(
        __file__, test_link_scraper_succeeds_in_qa.__name__[0] + f"_{str(test_id)}"
    )

    belief = Belief()
    shared_memory = SharedMemory(
        objective=objective,
        agent_pool=None,
    )

    link_scraper_action = LinkScraperAction(llm=llm)

    with patch.object(LinkScraperTool, "_run", side_effect=mock_run):
        task_agent = QAAgent(
            llm=llm,
            shared_memory=shared_memory,
            num_runs=3,
            actions=[link_scraper_action],
            validation_steps=3,
            belief=belief,
        )

        shared_memory.add(
            EventType.task,
            "Scraper",
            objective,
        )

        task_agent.run()

        results = shared_memory.get_by_type(EventType.result)
        logger.info(results[0].content)
        assert any(result[0] in results[0].content and
                   result[1] in results[0].content
                   for result in input_data), "Result not found in input_data"
        
