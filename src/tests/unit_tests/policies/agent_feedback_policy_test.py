from unittest.mock import patch

import pytest

from sherpa_ai.actions import EmptyAction
from sherpa_ai.agents import UserAgent
from sherpa_ai.events import Event, EventType
from sherpa_ai.memory import SharedMemory
from sherpa_ai.memory.belief import Belief
from sherpa_ai.policies.agent_feedback_policy import AgentFeedbackPolicy
from sherpa_ai.test_utils.llms import get_llm


@pytest.fixture
def mock_agent_run():
    with patch("sherpa_ai.agents.UserAgent.run") as mock_run:
        mock_run.return_value = "user response!"
        yield mock_run


def test_agent_feedback_policy(mock_agent_run, get_llm):  # noqa: F811
    llm = get_llm(__file__, test_agent_feedback_policy.__name__)

    shared_memory = SharedMemory(objective="")
    agent = UserAgent("Agent", "An agent to help the user", shared_memory=shared_memory)
    policy = AgentFeedbackPolicy(
        agent=agent, llm=llm, role_description="", output_instruction=""
    )
    belief = Belief()
    belief.set_current_task(Event(EventType.task, "Agent", "task"))

    belief.actions = [
        EmptyAction(name="Deliberation"),
        EmptyAction(name="GoogleSearch"),
    ]

    policy_output = policy.select_action(belief)
    context = belief.get_context(llm.get_num_tokens)

    assert "user response!" in context
    assert (
        policy_output.action.name == "Deliberation"
        or policy_output.action.name == "GoogleSearch"
    )
