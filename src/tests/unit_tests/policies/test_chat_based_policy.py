import sys

from langchain_core.language_models.chat_models import BaseChatModel
from loguru import logger

from sherpa_ai.actions.empty import EmptyAction
from sherpa_ai.agents.qa_agent import QAAgent
from sherpa_ai.events import Event, EventType
from sherpa_ai.memory.belief import Belief
from sherpa_ai.memory.state_machine import SherpaStateMachine
from sherpa_ai.policies.chat_sm_policy import ChatStateMachinePolicy
from sherpa_ai.test_utils.llms import get_llm  # noqa: F401

logger.remove()
logger.add(sys.stderr, level="DEBUG", serialize=False)


def get_state_machine(belief):
    action_a = EmptyAction(
        name="action_a", args={"a": "alway set this to a"}, belief=belief
    )
    action_b = EmptyAction(belief=belief)
    action_c = EmptyAction(
        name="action_c", args={"c": "alway set this to c"}, belief=belief
    )

    sm = SherpaStateMachine(states=["A", "B", "C", "D"], initial="A")
    sm.update_transition("A_to_B_1", "A", "B", action=action_a)
    sm.update_transition("A_to_A", "A", "A", action=action_a)
    sm.update_transition("B_to_C", "B", "C", action=action_b)
    sm.update_transition("B_to_D", "B", "D", action=action_c)

    return sm


def get_policy(llm: BaseChatModel):
    return ChatStateMachinePolicy(
        llm=llm,
    )


def test_policy_prompts(get_llm):  # noqa: F811
    llm = get_llm(__file__, test_policy_prompts.__name__, is_chat=True)
    policy = get_policy(llm)
    belief = Belief()
    state_machine = get_state_machine(belief)
    belief.state_machine = state_machine

    belief.set_current_task(
        Event(
            EventType.task,
            "User",
            "Move to state D",
        )
    )
    # Add some dummy action history
    belief.update_internal(
        EventType.action,
        "assistant",
        "A_to_A",
        {"action": {"name": "action_a", "args": {"a": "a"}}},
    )

    belief.update_internal(
        EventType.action_output,
        "assistant",
        "Success!",
        {"result": "success"},
    )

    prompt_data = policy.get_prompt_data(belief, belief.get_actions())
    prompt = policy.chat_template.invoke(prompt_data)

    #  The prompt messages compose of 1 system message, 2 dummy action history and 1
    #  human instruction
    assert len(prompt.messages) == 4

    action_output = policy.select_action(belief)

    # Select the most reasonable action with the given prompt
    assert action_output.action.name == "A_to_B_1"
    assert action_output.args == {"a": "a"}


def test_chat_based_policy_with_agent(get_llm):  # noqa: F811
    llm = get_llm(__file__, test_chat_based_policy_with_agent.__name__, is_chat=True)
    policy = get_policy(llm)

    belief = Belief()
    state_machine = get_state_machine(belief)
    belief.state_machine = state_machine

    belief.set_current_task(
        Event(
            EventType.task,
            "User",
            "Move to state D",
        )
    )

    agent = QAAgent(
        llm=llm,
        belief=belief,
        policy=policy,
        max_runs=2,
    )

    result = agent.run()

    # The agent should be able to move to state D
    assert result.status == "success"
    assert len(belief.internal_events) == 4
    assert belief.get_state() == "D"
