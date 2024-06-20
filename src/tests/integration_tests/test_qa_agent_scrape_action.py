from sherpa_ai.actions.link_content_scraper import LinkContentScraper
from sherpa_ai.agents import QAAgent
from sherpa_ai.events import EventType
from sherpa_ai.memory import SharedMemory
from sherpa_ai.output_parsers import CitationValidation
from sherpa_ai.test_utils.llms import get_llm


def test_qa_agent_succeeds(get_llm):  # noqa: F811
    llm = get_llm(__file__, test_qa_agent_succeeds.__name__)

    shared_memory = SharedMemory(
        objective="Summarize this link  https://en.wikipedia.org/wiki/Wikipedia?",
        agent_pool=None,
    )

    citation_validation = CitationValidation()
    link_scraper = LinkContentScraper(
        role_description="Planner",
        task="Summarize this link  https://en.wikipedia.org/wiki/Wikipedia?",
        llm=llm,
    )

    task_agent = QAAgent(
        llm=llm,
        shared_memory=shared_memory,
        actions=[link_scraper],
        validations=[citation_validation],
    )

    shared_memory.add(
        EventType.task,
        "Planner",
        "Summarize this link  https://en.wikipedia.org/wiki/Wikipedia?",
    )

    task_agent.run()

    results = shared_memory.get_by_type(EventType.result)
    assert len(results) == 1
