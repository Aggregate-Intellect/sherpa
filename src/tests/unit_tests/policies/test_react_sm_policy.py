import pytest
from langchain_core.language_models import FakeListLLM
from loguru import logger

from sherpa_ai.actions import EmptyAction
from sherpa_ai.events import build_event
from sherpa_ai.memory.belief import Belief
from sherpa_ai.memory.state_machine import SherpaStateMachine
from sherpa_ai.policies.react_sm_policy import ReactStateMachinePolicy


@pytest.fixture
def prepare_sm():
    action_a = EmptyAction()
    action_b = EmptyAction()
    action_c = EmptyAction()

    states = [
        {"name": "A", "description": "This is state A"},
        {"name": "B", "description": "This is state B"},
        {"name": "C", "description": "This is state C"},
    ]

    transitions = [
        {
            "trigger": "A_to_B_1",
            "source": "A",
            "dest": "B",
            "action": action_a,
            "description": "Transition 1",
        },
        {
            "trigger": "A_to_B_2",
            "source": "A",
            "dest": "B",
            "action": action_b,
            "description": "Transition 2",
        },
        {
            "trigger": "B_to_C",
            "source": "B",
            "dest": "C",
            "action": action_c,
            "description": "Transition 3",
        },
    ]

    sm = SherpaStateMachine(states=states, initial="A")

    for transition in transitions:
        sm.update_transition(**transition)
    return sm, states, transitions


def test_react_sm_policy_prompt_a(prepare_sm):
    state_machine, states, transitions = prepare_sm
    belief = Belief()
    belief.set_current_task("Task")
    belief.state_machine = state_machine

    policy = ReactStateMachinePolicy(
        role_description="Role Description",
        output_instruction="Output Instruction",
        llm=FakeListLLM(responses=[]),
    )

    actions = belief.get_actions()
    prompt = policy.get_prompt(belief, actions)

    logger.debug(prompt)

    assert states[0]["description"] in prompt
    assert states[1]["description"] not in prompt
    assert states[2]["description"] not in prompt
    assert transitions[0]["description"] in prompt
    assert transitions[1]["description"] in prompt
    assert transitions[2]["description"] not in prompt


def test_react_sm_policy_prompt_b(prepare_sm):
    state_machine, states, transitions = prepare_sm
    belief = Belief()
    belief.set_current_task("Task")
    belief.state_machine = state_machine

    policy = ReactStateMachinePolicy(
        role_description="Role Description",
        output_instruction="Output Instruction",
        llm=FakeListLLM(responses=[]),
    )

    # Go to state B
    state_machine.A_to_B_1()
    actions = belief.get_actions()
    prompt = policy.get_prompt(belief, actions)

    logger.debug(prompt)

    assert states[0]["description"] not in prompt
    assert states[1]["description"] in prompt
    assert states[2]["description"] not in prompt
    assert transitions[0]["description"] not in prompt
    assert transitions[1]["description"] not in prompt
    assert transitions[2]["description"] in prompt


def test_react_sm_policy_prompt_c(prepare_sm):
    state_machine, states, transitions = prepare_sm
    belief = Belief()
    belief.set_current_task("Task")
    belief.state_machine = state_machine

    policy = ReactStateMachinePolicy(
        role_description="Role Description",
        output_instruction="Output Instruction",
        llm=FakeListLLM(responses=[]),
    )

    # Go to state B
    state_machine.A_to_B_1()
    # Go to state C
    state_machine.B_to_C()

    actions = belief.get_actions()
    prompt = policy.get_prompt(belief, actions)

    logger.debug(prompt)

    assert states[0]["description"] not in prompt
    assert states[1]["description"] not in prompt
    assert states[2]["description"] in prompt
    assert transitions[0]["description"] not in prompt
    assert transitions[1]["description"] not in prompt
    assert transitions[2]["description"] not in prompt
