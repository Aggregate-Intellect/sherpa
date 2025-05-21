import pytest

from sherpa_ai.actions.base import AsyncBaseAction
from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.config.task_result import TaskResult
from sherpa_ai.events import build_event
from sherpa_ai.memory import Belief
from sherpa_ai.policies.base import BasePolicy
from sherpa_ai.runtime import ThreadedRuntime


class MockAsyncAction(AsyncBaseAction):
    name: str = "mock_async_action"
    args: list = []
    usage: str = "A mock async action for testing"

    async def execute(self, **kwargs):
        return self.belief.internal_events[0].content


class MockPolicy(BasePolicy):
    def select_action(self, belief):
        return type(
            "obj", (object,), {"action": MockAsyncAction(belief=belief), "args": {}}
        )

    async def async_select_action(self, belief):
        return type(
            "obj", (object,), {"action": MockAsyncAction(belief=belief), "args": {}}
        )


class MockAgent(BaseAgent):
    name: str = "mock_agent"
    description: str = "A mock agent for testing"

    def create_actions(self):
        return [MockAsyncAction(belief=self.belief)]

    def synthesize_output(self):
        return self.belief.get("mock_async_action")


@pytest.fixture()
def agent_runtime():
    belief = Belief()
    agent = MockAgent(belief=belief, policy=MockPolicy())
    runtime = ThreadedRuntime.start(agent=agent)
    yield runtime
    runtime.stop()


def test_sending_event(agent_runtime):
    event = build_event("message", "input_message", content="test input message")
    future = agent_runtime.ask(event, block=False)
    result = future.get()

    assert isinstance(result, TaskResult)
    assert result.status == "success"
    assert result.content == "test input message"
