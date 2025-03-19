import pytest

from sherpa_ai.actions.belief_actions import RetrieveBelief, UpdateBelief
from sherpa_ai.agents.qa_agent import QAAgent
from sherpa_ai.events import EventType
from sherpa_ai.memory.belief import Belief
from sherpa_ai.memory.shared_memory import SharedMemory
from sherpa_ai.test_utils.llms import get_llm


@pytest.fixture
def get_actions_belief():
    belief = Belief()
    belief.set("a.b", "1")
    belief.set("a.c", "2")
    belief.set("a.d.e", "3")
    belief.set("a.d.f", "4")

    acitons = [UpdateBelief(belief=belief), RetrieveBelief(belief=belief)]
    return acitons, belief


def test_update_belief(get_llm, get_actions_belief):
    llm = get_llm(__file__, test_update_belief.__name__, model_name="gpt-4o-mini")
    actions, belief = get_actions_belief

    shared_memory = SharedMemory(
        objective="Help user to complete the task",
        agent_pool=None,
    )

    task_agent = QAAgent(
        llm=llm,
        num_runs=1,
        shared_memory=shared_memory,
        actions=actions,
        description="You are a helpful agent help user to complete the task",
        do_synthesize_output=True
    )

    shared_memory.add(
        EventType.task,
        "User",
        "Remember that the answer value to question q1 is 42",
    )

    task_agent.run()

    assert belief.get("a.b") == "1"
    assert belief.get("a.c") == "2"
    assert belief.get("a.d.e") == "3"
    assert belief.get("a.d.f") == "4"
    assert belief.get("q1") == "42"


def test_update_belief_nested(get_llm, get_actions_belief):
    llm = get_llm(__file__, test_update_belief_nested.__name__, model_name="gpt-4o-mini")
    actions, belief = get_actions_belief

    shared_memory = SharedMemory(
        objective="Help user to complete the task",
        agent_pool=None,
    )

    task_agent = QAAgent(
        llm=llm,
        num_runs=1,
        shared_memory=shared_memory,
        actions=actions,
        description="You are a helpful agent help user to complete the task",
        do_synthesize_output=True
    )

    shared_memory.add(
        EventType.task,
        "User",
        "Remember that the name of p1 is 'Sherpa'",
    )

    task_agent.run()

    assert belief.get("a.b") == "1"
    assert belief.get("a.c") == "2"
    assert belief.get("a.d.e") == "3"
    assert belief.get("a.d.f") == "4"
    assert belief.get("p1.name") == "Sherpa"


def test_update_belief_exist(get_llm, get_actions_belief):
    llm = get_llm(__file__, test_update_belief_exist.__name__, model_name="gpt-4o-mini")
    actions, belief = get_actions_belief

    shared_memory = SharedMemory(
        objective="Help user to complete the task",
        agent_pool=None,
    )

    task_agent = QAAgent(
        llm=llm,
        num_runs=1,
        shared_memory=shared_memory,
        actions=actions,
        description="You are a helpful agent help user to complete the task",
        do_synthesize_output=True
    )

    shared_memory.add(
        EventType.task,
        "User",
        "Remember that property c of a is 3",
    )

    task_agent.run()

    assert belief.get("a.b") == "1"
    assert belief.get("a.c") == "3"
    assert belief.get("a.d.e") == "3"
    assert belief.get("a.d.f") == "4"


def test_retrieve_value(get_llm, get_actions_belief):
    llm = get_llm(__file__, test_retrieve_value.__name__, model_name="gpt-4o-mini")
    actions, belief = get_actions_belief

    shared_memory = SharedMemory(
        objective="Help user to complete the task",
        agent_pool=None,
    )

    task_agent = QAAgent(
        llm=llm,
        num_runs=1,
        shared_memory=shared_memory,
        actions=actions,
        description="You are a helpful agent help user to complete the task",
        do_synthesize_output=True
    )

    shared_memory.add(
        EventType.task,
        "User",
        "What is value of b of a?",
    )

    task_agent.run()

    results = shared_memory.get_by_type(EventType.result)

    assert "1" in results[0].content


def test_retrieve_and_calculate(get_llm, get_actions_belief):
    llm = get_llm(__file__, test_retrieve_and_calculate.__name__, model_name="gpt-4o-mini")
    actions, belief = get_actions_belief

    shared_memory = SharedMemory(
        objective="Help user to complete the task",
        agent_pool=None,
    )

    task_agent = QAAgent(
        llm=llm,
        num_runs=2,
        shared_memory=shared_memory,
        actions=actions,
        description="You are a helpful agent help user to complete the task",
        do_synthesize_output=True
    )

    shared_memory.add(
        EventType.task,
        "User",
        "What is the sum of the value of e and value of f in d of a?",
    )

    task_agent.run()

    results = task_agent.synthesize_output()

    assert "7" in results
