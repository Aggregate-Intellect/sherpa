"""Regression tests for Sherpa issue #265."""

import asyncio
from unittest.mock import AsyncMock, patch

from pydantic import Field

from sherpa_ai.actions.base import BaseAction
from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.agents.qa_agent import QAAgent
from sherpa_ai.config.task_result import TaskResult
from sherpa_ai.events import build_event
from sherpa_ai.memory.belief import Belief


class FakeSearch(BaseAction):
    """A search action that records queries without using Google."""

    name: str = "Google Search"
    usage: str = "Search the web"
    args: dict = {"query": "string"}
    queries: list[str] = Field(default_factory=list)

    def execute(self, query: str) -> str:
        self.queries.append(query)
        return f"Found information about {query}"


def make_agent(question, previous_answer):
    belief = Belief()
    belief.set_current_task(question)

    if previous_answer:
        belief.update(
            build_event(
                "result",
                "Sherpa",
                content=previous_answer,
            )
        )

    search = FakeSearch(belief=belief)
    agent = QAAgent(belief=belief, actions=[search])

    return agent, search


def run_recovery(agent):
    # Isolate the recovery preflight from the normal agent loop.
    completed = TaskResult(content="done", status="success")

    with patch.object(
        BaseAgent,
        "async_run",
        new_callable=AsyncMock,
        return_value=completed,
    ) as normal_run:
        result = asyncio.run(agent.async_run())
        normal_run.assert_awaited_once()

    return result


def test_missing_subject_triggers_new_search():
    agent, search = make_agent(
        "Compare with LangChain",
        "I couldn't find any information about LangChain.",
    )

    result = run_recovery(agent)

    assert result.status == "success"
    assert search.queries == ["LangChain documentation overview"]


def test_unrelated_question_does_not_retry():
    agent, search = make_agent(
        "Explain Python decorators",
        "I couldn't find any information about LangChain.",
    )

    run_recovery(agent)

    assert search.queries == []


def test_successful_previous_answer_does_not_retry():
    agent, search = make_agent(
        "Tell me more about LangChain",
        "LangChain is a framework for LLM applications.",
    )

    run_recovery(agent)

    assert search.queries == []


def test_recovery_is_limited_to_one_search():
    agent, search = make_agent(
        "Compare with LangChain",
        "I couldn't find any information about LangChain.",
    )

    run_recovery(agent)

    assert len(search.queries) == 1


def test_latest_answer_takes_priority():
    agent, search = make_agent(
        "Tell me more about LangChain",
        "I couldn't find any information about LangChain.",
    )

    agent.belief.update(
        build_event(
            "result",
            "Sherpa",
            content="LangChain is a framework for LLM applications.",
        )
    )

    run_recovery(agent)

    assert search.queries == []
