"""Regression coverage for retrieval recovery (issue #265)."""

from langchain_core.language_models import FakeListLLM

from sherpa_ai.actions.empty import EmptyAction
from sherpa_ai.events import build_event
from sherpa_ai.memory.belief import Belief
from sherpa_ai.policies.react_policy import ReactPolicy


def test_follow_up_search_keeps_current_context_and_recovery_instruction():
    llm = FakeListLLM(
        responses=[
            '{"command": {"name": "Google Search", '
            '"args": {"query": "LangChain framework documentation"}}}'
        ]
    )
    policy = ReactPolicy(
        role_description="Research assistant",
        output_instruction="Choose an action",
        llm=llm,
    )
    belief = Belief()
    belief.set_current_task("Compare with LangChain")
    belief.update(
        build_event(
            "result",
            "Sherpa",
            content="I couldn't find any information about LangChain.",
        )
    )
    belief.update_internal(
        "action_finish",
        "Google Search",
        outputs="Earlier query only searched LlamaIndex",
    )
    search = EmptyAction(name="Google Search", args={"query": "string"})
    belief.set_actions([search])

    captured = {}
    original = policy.prompt_template.format_prompt

    def capture(*args, **kwargs):
        captured.update(kwargs.get("variables", {}))
        return original(*args, **kwargs)

    policy.prompt_template.format_prompt = capture
    selected = policy.select_action(belief)

    assert selected.action is search
    assert selected.args == {"query": "LangChain framework documentation"}
    assert "couldn't find any information" in captured["task_context"]
    assert "Previous" in captured["output_instruction"] or "previous" in captured["output_instruction"]
    assert "targeted query" in captured["output_instruction"]
    assert "Compare with LangChain" == captured["task_description"]
