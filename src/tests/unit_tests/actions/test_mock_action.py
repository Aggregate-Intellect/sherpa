import pytest

from sherpa_ai.actions.mock import MockAction
from sherpa_ai.memory import Belief


def test_mock_action_constructs_without_a_belief():
    """MockAction must be usable without a belief.

    BaseAction.belief is typed `Belief`, and pydantic validates explicitly
    passed values even when the field default is None. MockAction forwarded
    belief=None unconditionally, so every construction raised ValidationError
    -- including the example in its own docstring.
    """
    action = MockAction(name="test_action", return_value="success")
    assert action.execute() == "success"


def test_mock_action_accepts_a_belief():
    belief = Belief()
    action = MockAction(name="test_action", belief=belief, return_value="ok")
    assert action.belief is belief
    assert action.execute() == "ok"


def test_mock_action_defaults():
    action = MockAction(name="test_action")
    assert action.execute() == "Mock result"
    assert action.name == "test_action"
    assert action.usage == "Mock usage"


@pytest.mark.parametrize("return_value", ["", "multi\nline", "unicode ✓"])
def test_mock_action_returns_value_verbatim(return_value):
    assert MockAction(name="a", return_value=return_value).execute() == return_value
