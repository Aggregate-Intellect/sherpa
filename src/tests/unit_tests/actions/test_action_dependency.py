# Tests for the dependency handling of action arguments in the BaseAction

from sherpa_ai.actions.base import BaseAction
from sherpa_ai.memory import Belief


class MockAction(BaseAction):
    name: str = "mock_action"
    usage: str = "Mock action for testing"
    arg_value_dict: dict

    def execute(self, **kwargs) -> str:
        for key, value in self.arg_value_dict.items():
            assert kwargs[key] == value

        return "success"


def test_args_from_belief():
    belief = Belief()
    belief.set("test_arg", "test_value")
    action = MockAction(
        args={"test_arg": {"type": "str", "source": "belief"}},
        belief=belief,
        arg_value_dict={"test_arg": "test_value"},
    )

    action()


def test_args_from_belief_and_agent():
    belief = Belief()
    belief.set("test_arg", "test_value")
    action = MockAction(
        args={
            "test_arg": {"type": "str", "source": "belief"},
            "test_arg2": {"type": "str", "source": "agent"},
        },
        belief=belief,
        arg_value_dict={"test_arg": "test_value", "test_arg2": "test_value2"},
    )

    action(test_arg2="test_value2")


def test_args_from_belief_key():
    belief = Belief()
    belief.set("arg1", "test_value")
    action = MockAction(
        args={
            "test_arg": {"type": "str", "source": "belief", "key": "arg1"},
            "test_arg2": {"type": "str", "source": "agent"},
        },
        belief=belief,
        arg_value_dict={"test_arg": "test_value", "test_arg2": "test_value2"},
    )

    action(test_arg2="test_value2")


def test_store_action_result():
    belief = Belief()
    action = MockAction(
        name="mock_action",
        args={},
        belief=belief,
        arg_value_dict={},
    )

    action()
    assert belief.get("mock_action") == "success"


def test_store_action_result_with_key():
    belief = Belief()
    action = MockAction(
        args={},
        belief=belief,
        arg_value_dict={},
        output_key="output_key",
    )

    action()
    assert belief.get("output_key") == "success"


def test_missing_argument_belief():
    belief = Belief()
    action = MockAction(
        args={"test_arg": {"type": "str", "source": "belief"}},
        belief=belief,
        arg_value_dict={},
    )

    try:
        action()
    except ValueError as e:
        assert str(e) == "Missing argument in belief: test_arg"


def test_missing_argument_agent():
    belief = Belief()
    action = MockAction(
        args={"test_arg": {"type": "str", "source": "agent"}},
        belief=belief,
        arg_value_dict={},
    )

    try:
        action()
    except ValueError as e:
        assert str(e) == "Missing argument from input: test_arg"


def test_action_to_string():
    belief = Belief()
    action = MockAction(
        args={
            "test_arg1": {"type": "str", "source": "belief"},
            "test_arg2": {"type": "str", "source": "agent"},
        },
        belief=belief,
        arg_value_dict={"test_arg1": "test_value", "test_arg2": "test_value2"},
    )

    action_string = str(action)

    assert "test_arg2" in action_string
    assert "test_arg1" not in action_string


def test_action_sequence():
    belief = Belief()
    belief.set("test_arg", "test_value")

    action1 = MockAction(
        args={"test_arg": {"type": "str", "source": "belief"}},
        belief=belief,
        arg_value_dict={"test_arg": "test_value"},
        output_key="out1",
    )

    action2 = MockAction(
        args={"test_arg": {"type": "str", "source": "belief", "key": "out1"}},
        belief=belief,
        arg_value_dict={"test_arg": "success"},
        output_key="out2",
    )

    action1()
    action2()

    assert belief.get("out1") == "success"
    assert belief.get("out2") == "success"
