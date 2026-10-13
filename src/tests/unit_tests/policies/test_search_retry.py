"""Regression tests for issue #265: recovery after an incomplete search."""

from langchain_core.language_models import FakeListLLM
from pydantic import Field
from pydantic import Field

from sherpa_ai.actions.base import BaseAction
from sherpa_ai.memory.belief import Belief
from sherpa_ai.events import build_event
from sherpa_ai.policies.react_policy import ReactPolicy


class FakeSearch(BaseAction):
    """Record search queries without calling Google."""

    name: str = "Google Search"
    usage: str = "Search the web for information"
    args: dict = {"query": "string"}
    queries: list[str] = Field(default_factory=list)
    queries: list[str] = Field(default_factory=list)

    def execute(self, query: str) -> str:
        # Keep a record of every search the agent makes.
        self.queries.append(query)

        if "langchain" in query.lower():
            return "LangChain is a framework for building LLM applications."

        if "llamaindex" in query.lower():
            return "LlamaIndex is a framework for connecting LLMs to data."

        return "No results found."


def test_agent_searches_again_after_missing_information():
    # Simulate the action choices made on two consecutive turns.
    llm = FakeListLLM(
        responses=[
            '{"command": {"name": "Google Search", '
            '"args": {"query": "LlamaIndex"}}}',
            '{"command": {"name": "Google Search", '
            '"args": {"query": "LangChain framework documentation"}}}',
        ]
    )

    policy = ReactPolicy(
        role_description="Research assistant",
        output_instruction="Choose the next action",
        llm=llm,
    )

    search = FakeSearch()

    belief = Belief()
    belief.set_actions([search])

    # First turn: the agent searches only for LlamaIndex.
    belief.set_current_task("Compare LlamaIndex and LangChain")

    first_action = policy.select_action(belief)
    first_result = first_action.action.execute(**first_action.args)

    assert "LlamaIndex" in first_result
    assert search.queries == ["LlamaIndex"]

    # Save the incomplete answer in conversation history.
    belief.update(
        build_event(
            "result",
            "Sherpa",
            content=(
                "LlamaIndex connects language models to data. "
                "I couldn't find information about LangChain."
            ),
        )
    )

    # Second turn: the user asks about the missing framework.
    belief.set_current_task("Compare with LangChain")

    second_action = policy.select_action(belief)
    second_result = second_action.action.execute(**second_action.args)

    # A new search must occur, not a repetition of the failed answer.
    assert len(search.queries) == 2
    assert "langchain" in search.queries[1].lower()
    assert "LangChain is a framework" in second_result


