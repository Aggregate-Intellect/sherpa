import pytest

from sherpa_ai.actions.empty import EmptyAction
from sherpa_ai.memory.belief import Belief
from sherpa_ai.memory.state_machine import SherpaStateMachine


@pytest.fixture
def state_machine():
    action_a = EmptyAction()
    action_b = EmptyAction()
    action_c = EmptyAction()

    sm = SherpaStateMachine(states=["A", "B", "C"], initial="A")
    sm.add_transition("A_to_B_1", "A", "B", action=action_a)
    sm.add_transition("A_to_B_2", "A", "B", action=action_b)
    sm.add_transition("B_to_C", "B", "C", action=action_c)

    return sm


def test_get_actions(state_machine):
    assert state_machine.state == "A"

    actions = state_machine.get_actions()

    assert len(actions) == 2
    assert actions[0].name == "A_to_B_1"
    assert actions[1].name == "A_to_B_2"


def test_transition(state_machine):
    state_machine.A_to_B_1()

    assert state_machine.state == "B"
    actions = state_machine.get_actions()

    assert len(actions) == 1
    assert actions[0].name == "B_to_C"

    state_machine.B_to_C()

    assert state_machine.state == "C"

    actions = state_machine.get_actions()

    assert len(actions) == 0


def test_beliefs(state_machine):
    belief = Belief()
    belief.state_machine = state_machine

    assert belief.get_state() == "A"

    actions = belief.get_actions()

    assert len(actions) == 2
    assert actions[0].name == "A_to_B_1"
    assert actions[1].name == "A_to_B_2"

    actions[0].execute()

    assert belief.get_state() == "B"

    actions = belief.get_actions()

    assert len(actions) == 1
    assert actions[0].name == "B_to_C"

    actions[0].execute()

    assert belief.get_state() == "C"

    actions = belief.get_actions()

    assert len(actions) == 0
