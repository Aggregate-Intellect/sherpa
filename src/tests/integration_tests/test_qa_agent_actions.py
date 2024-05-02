import pytest

from sherpa_ai.actions import ArxivSearch, GoogleSearch
from sherpa_ai.agents import QAAgent
from sherpa_ai.events import EventType
from sherpa_ai.memory import SharedMemory
from sherpa_ai.output_parsers import CitationValidation
from sherpa_ai.test_utils.llms import get_llm


def test_qa_agent_succeeds(get_llm):  # noqa: F811
    llm = get_llm(__file__, test_qa_agent_succeeds.__name__)

    shared_memory = SharedMemory(
        objective="What is AutoGPT?",
        agent_pool=None,
    )

    citation_validation = CitationValidation()
    google_search = GoogleSearch(
        role_description="Planner",
        task="What is AutoGPT?",
        llm=llm,
        include_metadata=True,
    )

    task_agent = QAAgent(
        llm=llm,
        shared_memory=shared_memory,
        actions=[google_search],
        validations=[citation_validation],
    )

    shared_memory.add(
        EventType.task,
        "Planner",
        "What is AutoGPT?",
    )

    task_agent.run()

    results = shared_memory.get_by_type(EventType.result)
    assert len(results) == 1


def test_qa_agent_citation_validation_no_action(get_llm):  # noqa: F811
    llm = get_llm(__file__, test_qa_agent_citation_validation_no_action.__name__)

    shared_memory = SharedMemory(
        objective="What is AutoGPT?",
        agent_pool=None,
    )

    citation_validation = CitationValidation()

    task_agent = QAAgent(
        llm=llm, shared_memory=shared_memory, validations=[citation_validation]
    )

    shared_memory.add(
        EventType.task,
        "Planner",
        "What is AutoGPT?",
    )

    task_agent.run()

    results = shared_memory.get_by_type(EventType.result)
    assert len(results) == 1


def test_qa_agent_citation_validation_multiple_action(get_llm):  # noqa: F811
    # Make sure the citation validation works even when the the action providing citation is not selected
    llm = get_llm(__file__, test_qa_agent_citation_validation_multiple_action.__name__)

    shared_memory = SharedMemory(
        objective="What is AutoGPT?",
        agent_pool=None,
    )

    citation_validation = CitationValidation()
    google_search = GoogleSearch(
        role_description="Planner",
        task="What is AutoGPT?",
        llm=llm,
        include_metadata=True,
    )
    arxiv_search = ArxivSearch(
        role_description="Planner",
        task="What is AutoGPT?",
        llm=llm,
    )

    task_agent = QAAgent(
        llm=llm,
        shared_memory=shared_memory,
        validations=[citation_validation],
        description="Always use ArxivSearch",
        actions=[arxiv_search, google_search],
    )

    shared_memory.add(
        EventType.task,
        "Planner",
        "What is AutoGPT?",
    )

    task_agent.run()

    results = shared_memory.get_by_type(EventType.result)
    assert len(results) == 1
