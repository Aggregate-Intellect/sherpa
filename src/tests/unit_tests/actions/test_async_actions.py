import pytest
from sherpa_ai.actions.base import AsyncBaseAction, ActionArgument
from sherpa_ai.memory import Belief

class MockAsyncAction(AsyncBaseAction):
    name: str = "mock_async_action"
    args: list = []
    usage: str = "A mock async action for testing"

    async def execute(self, **kwargs):
        return "async_result"

@pytest.mark.asyncio
async def test_async_action_execution():
    action = MockAsyncAction()
    result = await action()
    assert result == "async_result"

@pytest.mark.asyncio
async def test_async_action_with_belief():
    belief = Belief()
    action = MockAsyncAction(belief=belief)
    result = await action()
    assert result == "async_result"
    assert belief.get("mock_async_action") == "async_result"

@pytest.mark.asyncio
async def test_async_action_with_args():
    action = MockAsyncAction(args=[
        ActionArgument(
            name="test_arg",
            type="str",
            description="Test argument"
        )
    ])
    result = await action(test_arg="test_value")
    assert result == "async_result"

@pytest.mark.asyncio
async def test_async_action_with_belief_args():
    belief = Belief()
    belief.set("test_key", "test_value")
    action = MockAsyncAction(
        belief=belief,
        args=[
            ActionArgument(
                name="test_arg",
                type="str",
                description="Test argument",
                source="belief",
                key="test_key"
            )
        ]
    )
    result = await action()
    assert result == "async_result"
    
