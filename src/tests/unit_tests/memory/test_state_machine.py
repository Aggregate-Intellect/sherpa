import pytest
from loguru import logger
from transitions.extensions import AsyncMachine

from sherpa_ai.actions.empty import EmptyAction
from sherpa_ai.memory.belief import Belief
from sherpa_ai.memory.state_machine import SherpaStateMachine


@pytest.fixture
def state_machine():
    action_a = EmptyAction()
    action_b = EmptyAction()
    action_c = EmptyAction()

    sm = SherpaStateMachine(states=["A", "B", "C"], initial="A")
    sm.update_transition("A_to_B_1", "A", "B", action=action_a)
    sm.update_transition("A_to_B_2", "A", "B", action=action_b)
    sm.update_transition("B_to_C", "B", "C", action=action_c)

    return sm


@pytest.fixture
def async_state_machine():
    action_a = EmptyAction()
    action_b = EmptyAction()
    action_c = EmptyAction()

    async def mock_condition_True():
        return True

    async def mock_condition_False():
        return False

    sm = SherpaStateMachine(states=["A", "B", "C"], initial="A", sm_cls=AsyncMachine)
    sm.update_transition(
        "A_to_B_1", "A", "B", action=action_a, conditions=mock_condition_True
    )
    sm.update_transition(
        "A_to_B_2", "A", "B", action=action_b, conditions=mock_condition_False
    )
    sm.update_transition("B_to_C", "B", "C", action=action_c)

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


def test_extension_features():
    action_a = EmptyAction()
    action_b = EmptyAction()
    action_c = EmptyAction()
    states = [
        {"name": "A", "description": "This is state A", "tags": ["waiting"]},
        {"name": "B", "description": "This is state B"},
        {"name": "C", "description": "This is state C"},
    ]

    sm = SherpaStateMachine(states=states, initial="A")
    sm.update_transition(
        "A_to_B_1", "A", "B", action=action_a, description="Transition from A to B"
    )
    sm.update_transition(
        "A_to_B_2", "A", "B", action=action_b, description="Transition from A to B"
    )
    sm.update_transition(
        "B_to_C", "B", "C", action=action_c, description="Transition from B to C"
    )

    assert sm.sm.get_state("A").description == "This is state A"
    assert sm.sm.get_state("A").is_waiting
    assert sm.sm.get_state("B").description == "This is state B"
    assert sm.sm.get_state("C").description == "This is state C"

    assert sm.sm.get_transitions("A_to_B_1")[0].description == "Transition from A to B"
    assert sm.sm.get_transitions("A_to_B_2")[0].description == "Transition from A to B"
    assert sm.sm.get_transitions("B_to_C")[0].description == "Transition from B to C"

    assert sm.get_current_state().name == "A"
    assert sm.get_current_state().description == "This is state A"


@pytest.mark.asyncio
async def test_get_actions_async(async_state_machine):
    assert async_state_machine.state == "A"

    actions = await async_state_machine.async_get_actions()

    logger.error(actions)

    assert len(actions) == 1
    assert actions[0].name == "A_to_B_1"


def test_get_action_full_callbacks():
    action_on_exit = EmptyAction(usage="on_exit", args={"on_exit": "2"})
    action_before1 = EmptyAction(usage="before1", args={"before1": "3"})
    action_before2 = EmptyAction(usage="before2", args={"before2": "4"})
    action_on_enter1 = EmptyAction(usage="on_enter1", args={"on_enter1": "5"})
    action_on_enter2 = EmptyAction(usage="on_enter2", args={"on_enter2": "6"})
    action_after = EmptyAction(usage="after", args={"after": "7"})

    sm = SherpaStateMachine(
        states=[
            {"name": "A", "on_exit": action_on_exit},
            {"name": "B", "on_enter": [action_on_enter1, action_on_enter2]},
        ],
        initial="A",
    )
    sm.update_transition(
        "A_to_B",
        "A",
        "B",
        before=[action_before1, action_before2],
        after=action_after,
    )

    action = sm.get_actions()[0]

    args = {}

    for arg in action.args:
        args[arg.name] = arg.description

    assert args == {
        "on_exit": "2",
        "before1": "3",
        "before2": "4",
        "on_enter1": "5",
        "on_enter2": "6",
        "after": "7",
    }

    # assert action_prepare.usage in action.usage
    assert action_on_exit.usage in action.usage
    assert action_before1.usage in action.usage
    assert action_before2.usage in action.usage
    assert action_on_enter1.usage in action.usage
    assert action_on_enter2.usage in action.usage
    assert action_after.usage in action.usage
