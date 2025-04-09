from unittest.mock import patch
import socket

import pytest

from sherpa_ai.actions import ArxivSearch, GoogleSearch
from sherpa_ai.actions.mockaction import MockAction
from sherpa_ai.agents import QAAgent
from sherpa_ai.events import EventType
from sherpa_ai.memory import SharedMemory
from sherpa_ai.output_parsers import CitationValidation
from sherpa_ai.test_utils.llms import get_llm


@pytest.fixture
def mock_reranker():
    with patch("sherpa_ai.actions.base.BaseRetrievalAction.reranking") as mock_reranker:
        mock_reranker.side_effect = lambda x: x
        yield mock_reranker

def is_offline():
    try:
        # Try to connect to a DNS server (Cloudflare)
        socket.create_connection(("1.1.1.1", 53), timeout=2)
        return False
    except OSError:
        return True

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

    if is_offline():
        # Mock versions
        arxiv_search = MockAction(
            name="ArxivSearch",
            usage="Search arXiv for papers",
            return_value="AutoGPT is an AI tool from arXiv."
        )

        google_search = MockAction(
            name="GoogleSearch",
            usage="Search Google for relevant info",
            return_value="AutoGPT automates tasks."
        )

    else:
        # Orginal versions
        google_search = GoogleSearch(
            role_description="Planner",
            task="What is AutoGPT?",
            llm=llm,
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


def test_qa_agent_reranking(get_llm, mock_reranker):  # noqa: F811
    # Make sure the reranking can be triggered by an agent
    llm = get_llm(__file__, test_qa_agent_reranking.__name__)

    shared_memory = SharedMemory(
        objective="What is AutoGPT?",
        agent_pool=None,
    )

    citation_validation = CitationValidation()
    google_search = GoogleSearch(
        role_description="Planner",
        task="What is AutoGPT?",
        llm=llm,
        perform_reranking=True,
    )

    task_agent = QAAgent(
        llm=llm,
        num_runs=1,
        shared_memory=shared_memory,
        validations=[citation_validation],
        description="Use Google Search",
        actions=[google_search],
    )

    shared_memory.add(
        EventType.task,
        "Planner",
        "What is AutoGPT?",
    )

    task_agent.run()

    results = shared_memory.get_by_type(EventType.result)
    assert len(results) == 1

    mock_reranker.assert_called_once()
    assert google_search.current_task == "What is AutoGPT?"
