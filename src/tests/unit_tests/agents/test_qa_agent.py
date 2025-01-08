from loguru import logger

from sherpa_ai.actions.base import BaseAction
from sherpa_ai.actions.exceptions import SherpaActionExecutionException
from sherpa_ai.agents import QAAgent
from sherpa_ai.events import EventType
from sherpa_ai.memory import SharedMemory
from sherpa_ai.memory.belief import Belief
from sherpa_ai.policies.base import BasePolicy, PolicyOutput
from sherpa_ai.policies.exceptions import SherpaPolicyException
from sherpa_ai.test_utils.llms import get_llm  # noqa: F401


def test_task_agent_succeeds(get_llm):  # noqa: F811
    llm = get_llm(__file__, test_task_agent_succeeds.__name__)

    shared_memory = SharedMemory(
        objective="What is AutoGPT?",
        agent_pool=None,
    )

    task_agent = QAAgent(
        llm=llm,
        shared_memory=shared_memory,
    )

    shared_memory.add(
        EventType.task,
        "Planner",
        "What is AutoGPT?",
    )

    task_agent.run()

    results = shared_memory.get_by_type(EventType.result)
    assert len(results) == 1


def test_qa_agent_policy_selection_exception():
    actions = [MockAction(fail_count=0, exception_type=Exception)]
    policy = MockPolicy(fail_count=2, exception_type=SherpaPolicyException)

    belief = Belief()
    belief.set_actions(actions)

    agent = QAAgent(
        llm=None,
        belief=belief,
        actions=actions,
        policy=policy,
        max_runs=3,
    )

    result = agent.run()

    assert result.content == "success"


def test_qa_agent_policy_selection_failed():
    actions = [MockAction(fail_count=0, exception_type=Exception)]
    policy = MockPolicy(fail_count=2, exception_type=Exception)

    belief = Belief()
    belief.set_actions(actions)

    agent = QAAgent(
        llm=None,
        belief=belief,
        actions=actions,
        policy=policy,
        max_runs=3,
    )

    result = agent.run()
    assert "exception" in result.content.lower()


def test_qa_agent_action_execution_exception():
    actions = [MockAction(fail_count=2, exception_type=SherpaActionExecutionException)]
    policy = MockPolicy(fail_count=0, exception_type=Exception)

    belief = Belief()
    belief.set_actions(actions)

    agent = QAAgent(
        llm=None,
        belief=belief,
        actions=actions,
        policy=policy,
        max_runs=3,
    )

    result = agent.run()

    assert result.content == "success"


def test_qa_agent_action_execution_failed():
    actions = [MockAction(fail_count=2, exception_type=Exception)]
    policy = MockPolicy(fail_count=0, exception_type=Exception)

    belief = Belief()
    belief.set_actions(actions)

    agent = QAAgent(
        llm=None,
        belief=belief,
        actions=actions,
        policy=policy,
        max_runs=3,
    )

    result = agent.run()
    assert "exception" in result.content.lower()


class MockPolicy(BasePolicy):
    fail_count: int
    current_fail_count: int = 0
    exception_type: type

    def select_action(self, belief: Belief) -> PolicyOutput:
        if self.current_fail_count < self.fail_count:
            self.current_fail_count += 1
            raise self.exception_type("Policy selection failed")

        return PolicyOutput(action=belief.get_actions()[0], args={})


class MockAction(BaseAction):
    name: str = "mock_action"
    usage: str = "Mock action for testing"
    args: dict = {}

    fail_count: int
    current_fail_count: int = 0
    exception_type: type

    def execute(self, **kwargs) -> str:
        if self.current_fail_count < self.fail_count:
            self.current_fail_count += 1
            raise self.exception_type("Action execution failed")

        return "success"
