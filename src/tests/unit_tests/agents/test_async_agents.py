import pytest
from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.actions.base import AsyncBaseAction
from sherpa_ai.memory import Belief, SharedMemory
from sherpa_ai.policies.base import BasePolicy
from sherpa_ai.config.task_result import TaskResult

class MockAsyncAction(AsyncBaseAction):
    name: str = "mock_async_action"
    args: list = []
    usage: str = "A mock async action for testing"

    async def execute(self, **kwargs):
        return "async_result"

class MockPolicy(BasePolicy):
    def select_action(self, belief):
        return type('obj', (object,), {
            'action': MockAsyncAction(),
            'args': {}
        })

    async def async_select_action(self, belief):
        return type('obj', (object,), {
            'action': MockAsyncAction(),
            'args': {}
        })

class MockAgent(BaseAgent):
    name: str = "mock_agent"
    description: str = "A mock agent for testing"
    
    def create_actions(self):
        return [MockAsyncAction()]
    
    def synthesize_output(self):
        return self.belief.get("mock_async_action")

@pytest.mark.asyncio
async def test_async_send_event():
    agent = MockAgent(belief=Belief())
    await agent.async_send_event("test_event", {"test": "value"})
    # Since state_machine is None, it should just log an error and return

@pytest.mark.asyncio
async def test_async_select_action():
    agent = MockAgent(
        belief=Belief(),
        policy=MockPolicy()
    )
    result = await agent.async_select_action()
    assert result is not None
    assert isinstance(result.action, MockAsyncAction)
    assert result.args == {}

@pytest.mark.asyncio
async def test_async_run():
    agent = MockAgent(
        belief=Belief(),
        policy=MockPolicy()
    )
    result = await agent.async_run()
    assert isinstance(result, TaskResult)
    assert result.status == "success"
    assert result.content == "async_result"

@pytest.mark.asyncio
async def test_async_run_with_shared_memory():
    shared_memory = SharedMemory(objective="test objective")
    # Add a task to the shared memory
    shared_memory.add("task", "test_agent", content="test task")
    
    agent = MockAgent(
        belief=Belief(),
        policy=MockPolicy(),
        shared_memory=shared_memory
    )
    result = await agent.async_run()
    assert isinstance(result, TaskResult)
    assert result.status == "success"
    assert result.content == "async_result"

@pytest.mark.asyncio
async def test_async_act():
    agent = MockAgent(belief=Belief())
    action = MockAsyncAction()
    result = await agent.async_act(action, {})
    assert result == "async_result"
    
