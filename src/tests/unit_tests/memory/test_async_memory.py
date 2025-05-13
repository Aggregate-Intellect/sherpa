import pytest
from loguru import logger

from sherpa_ai.memory import Belief
from sherpa_ai.memory.state_machine import SherpaStateMachine, State
from sherpa_ai.actions.base import BaseAction, AsyncBaseAction
import transitions.extensions.asyncio as ts_async
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# Define Pydantic models for our actions
class MockAsyncActionModel(BaseModel):
    name: str = "mock_async_action"
    args: List[Any] = Field(default_factory=list)
    usage: str = "A mock async action for testing"

class MockSyncActionModel(BaseModel):
    name: str = "mock_sync_action"
    args: List[Any] = Field(default_factory=list)
    usage: str = "A mock sync action for testing"

# Action classes that use the Pydantic models
class MockAsyncAction(AsyncBaseAction):
    name: str = "mock_async_action"
    args: List[Any] = []
    usage: str = "A mock async action for testing"

    async def execute(self, **kwargs):
        return "async_result"
    
    def to_dict(self) -> Dict[str, Any]:
        return MockAsyncActionModel(
            name=self.name,
            args=self.args,
            usage=self.usage
        ).model_dump()

class MockSyncAction(BaseAction):
    name: str = "mock_sync_action"
    args: List[Any] = []
    usage: str = "A mock sync action for testing"

    def execute(self, **kwargs):
        return "sync_result"
    
    def to_dict(self) -> Dict[str, Any]:
        return MockSyncActionModel(
            name=self.name,
            args=self.args,
            usage=self.usage
        ).model_dump()

@pytest.mark.asyncio
async def test_belief_async_get_actions():
    belief = Belief()
    belief.actions = [MockAsyncAction(), MockSyncAction()]
    
    # Test without state machine
    actions = await belief.async_get_actions()
    assert len(actions) == 2
    assert isinstance(actions[0], MockAsyncAction)
    assert isinstance(actions[1], MockSyncAction)

@pytest.mark.asyncio
async def test_belief_async_get_action():
    belief = Belief()
    belief.actions = [MockAsyncAction(), MockSyncAction()]
    
    # Test getting async action
    action = await belief.async_get_action("mock_async_action")
    assert isinstance(action, MockAsyncAction)
    
    # Test getting sync action
    action = await belief.async_get_action("mock_sync_action")
    assert isinstance(action, MockSyncAction)
    
    # Test getting non-existent action
    action = await belief.async_get_action("non_existent")
    assert action is None

@pytest.mark.asyncio
async def test_state_machine_async_get_actions():
    # Create a state machine with async and sync actions
    states = ["initial", "final"]
    
    transitions = [
        {
            "trigger": "next",
            "source": "initial",
            "dest": "final"
        }
    ]
    
    sm = SherpaStateMachine(
        name="test_machine",
        states=states,
        transitions=transitions,
        initial="initial",
        sm_cls=ts_async.AsyncMachine  # Use AsyncMachine for async state machine
    )
    
    # Add the action after creating the state machine
    sm.update_transition("next", "initial", "final", action=MockAsyncAction())
    
    # Test getting actions from initial state
    actions = await sm.async_get_actions(include_waiting=True)
    assert len(actions) == 1
    # Check that the action has the expected properties
    action = actions[0]
    # Use attribute access for AsyncDynamicAction objects
    assert hasattr(action, "name")
    assert action.name == "next"
    assert hasattr(action, "args")
    assert hasattr(action, "usage")
    # Log the usage string for debugging
    logger.debug(f"Action usage: {action.usage}")
    # Check for any part of our mock action description
    assert "mock" in str(action.usage).lower() or "async" in str(action.usage).lower()

@pytest.mark.asyncio
async def test_state_machine_async_transition():
    # Create a state machine with async transition
    states = ["initial", "final"]
    
    transitions = [
        {
            "trigger": "next",
            "source": "initial",
            "dest": "final"
        }
    ]
    
    sm = SherpaStateMachine(
        name="test_machine",
        states=states,
        transitions=transitions,
        initial="initial",
        sm_cls=ts_async.AsyncMachine  # Use AsyncMachine for async state machine
    )
    
    # Add the action after creating the state machine
    sm.update_transition("next", "initial", "final", action=MockAsyncAction())
    
    # Test async transition
    assert sm.state == "initial"
    # Use await for async state machine
    await sm.next()
    assert sm.state == "final"

@pytest.mark.asyncio
async def test_belief_with_state_machine():
    belief = Belief()
    
    # Create a state machine with async action
    states = ["initial", "final"]
    
    transitions = [
        {
            "trigger": "next",
            "source": "initial",
            "dest": "final"
        }
    ]
    
    sm = SherpaStateMachine(
        name="test_machine",
        states=states,
        transitions=transitions,
        initial="initial",
        sm_cls=ts_async.AsyncMachine  # Use AsyncMachine for async state machine
    )
    
    # Add the action after creating the state machine
    sm.update_transition("next", "initial", "final", action=MockAsyncAction())
    
    belief.state_machine = sm
    
    # Test getting actions through belief
    actions = await belief.async_get_actions()
    assert len(actions) == 1
    # Check that the action has the expected properties
    action = actions[0]
    # Use attribute access for AsyncDynamicAction objects
    assert hasattr(action, "name")
    assert action.name == "next"
    assert hasattr(action, "args")
    assert hasattr(action, "usage")
    # Log the usage string for debugging
    logger.debug(f"Action usage: {action.usage}")
    # Check for any part of our mock action description
    assert "mock" in str(action.usage).lower() or "async" in str(action.usage).lower()
    
    # Test getting specific action
    action = await belief.async_get_action("next")
    assert hasattr(action, "name")
    assert action.name == "next"
    
