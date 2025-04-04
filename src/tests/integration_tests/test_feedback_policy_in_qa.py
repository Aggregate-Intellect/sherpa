from unittest.mock import patch

import pytest

from sherpa_ai.actions.google_search import GoogleSearch
from sherpa_ai.agents.qa_agent import QAAgent
from sherpa_ai.agents.user import UserAgent
from sherpa_ai.memory import SharedMemory
from sherpa_ai.policies.agent_feedback_policy import AgentFeedbackPolicy
from sherpa_ai.test_utils.llms import get_llm


def mock_user_run_more_info():
    return "Which planet is biggest, Earth, Mars or Jupiter?"


def mock_user_run_google_search():
    return "Google search the question"


@pytest.fixture
def mock_google_search():
    with patch("sherpa_ai.actions.google_search.GoogleSearch.search") as mock_run:
        mock_run.return_value = [
            {"Source": "source1", "Document": "Jupiter is the biggest planet"}
        ]
        yield mock_run


def test_feedback_policy_in_qa_incomplete(get_llm, mock_google_search):
    test_id = 0
    llm = get_llm(
        __file__,
        test_feedback_policy_in_qa_incomplete.__name__ + f"_{str(test_id)}",
        model_name="gpt-4o-mini",
    )
    question = "What is the biggest ?"
    shared_memory = SharedMemory(agent_pool=None, objective=" Answer the question")

    google_search = GoogleSearch(
        role_description="Act as a question answering agent",
        task=" Question answering",
        llm=llm,
    )

    agent = UserAgent(name="Agent", description="", shared_memory=shared_memory)
    agent.run = mock_user_run_more_info

    policy = AgentFeedbackPolicy(
        agent=agent, llm=llm, role_description="", output_instruction=""
    )
    qa_agent = QAAgent(
        llm=llm,
        shared_memory=shared_memory,
        num_runs=3,
        actions=[google_search],
        policy=policy,
    )
    qa_agent.shared_memory.add("task", "human", content=question)

    result = qa_agent.run()

    assert "Jupiter" in result.content


def test_feedback_policy_in_qa_complete(get_llm, mock_google_search):
    test_id = 0
    llm = get_llm(
        __file__,
        test_feedback_policy_in_qa_complete.__name__ + f"_{str(test_id)}",
        model_name="gpt-4o-mini",
    )
    question = "What is the biggest?, Jupyter, Mars or Earth?"
    shared_memory = SharedMemory(agent_pool=None, objective=" Answer the question")

    google_search = GoogleSearch(
        role_description="Act as a question answering agent",
        task=" Question answering",
        llm=llm,
    )

    agent = UserAgent(name="Agent", description="", shared_memory=shared_memory)
    agent.run = mock_user_run_google_search

    policy = AgentFeedbackPolicy(
        agent=agent, llm=llm, role_description="", output_instruction=""
    )
    qa_agent = QAAgent(
        llm=llm,
        shared_memory=shared_memory,
        num_runs=3,
        actions=[google_search],
        policy=policy,
    )
    qa_agent.shared_memory.add("task", "human", content=question)

    result = qa_agent.run()

    assert "Jupiter" in result.content
