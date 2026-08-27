"""Tests for DecisionEvent recording and state machine visualization."""

import pytest

from sherpa_ai.actions.empty import EmptyAction
from sherpa_ai.events import DecisionEvent, build_event
from sherpa_ai.memory.belief import Belief
from sherpa_ai.memory.state_machine import SherpaStateMachine
from sherpa_ai.visualization.state_machine_viewer import (
    DecisionRecord,
    StateMachineViewer,
)


def test_decision_event_creation():
    event = DecisionEvent(
        name="agent_1", chosen="A_to_B_1", alternatives=["A_to_B_2"], state="A",
    )
    assert event.event_type == "decision"
    assert event.chosen == "A_to_B_1"
    assert event.alternatives == ["A_to_B_2"]
    assert event.state == "A"


def test_decision_event_frozen_type():
    event = DecisionEvent(name="test", chosen="x", alternatives=[])
    assert event.event_type == "decision"


def test_build_event_decision():
    event = build_event(
        "decision", "agent_1",
        chosen="action_a", alternatives=["action_b", "action_c"], state="idle",
    )
    assert isinstance(event, DecisionEvent)
    assert event.chosen == "action_a"
    assert event.alternatives == ["action_b", "action_c"]
    assert event.state == "idle"


def test_belief_records_decision():
    belief = Belief()
    belief.update_internal(
        "decision", "agent_1",
        chosen="search", alternatives=["deliberate", "summarize"], state="researching",
    )
    assert len(belief.internal_events) == 1
    event = belief.internal_events[0]
    assert isinstance(event, DecisionEvent)
    assert event.chosen == "search"


def test_belief_get_by_type_decision():
    belief = Belief()
    belief.update_internal("action_start", "agent_1", args={"query": "test"})
    belief.update_internal(
        "decision", "agent_1", chosen="search", alternatives=["deliberate"], state="A",
    )
    belief.update_internal("action_finish", "agent_1", outputs="result")
    decisions = belief.get_by_type("decision")
    assert len(decisions) == 1
    assert decisions[0].chosen == "search"


@pytest.fixture
def belief_with_sm():
    action_a = EmptyAction()
    action_b = EmptyAction()
    action_c = EmptyAction()
    sm = SherpaStateMachine(states=["A", "B", "C"], initial="A")
    sm.update_transition("A_to_B_1", "A", "B", action=action_a)
    sm.update_transition("A_to_B_2", "A", "B", action=action_b)
    sm.update_transition("B_to_C", "B", "C", action=action_c)
    belief = Belief()
    belief.state_machine = sm
    belief.update_internal(
        "decision", "test_agent",
        chosen="A_to_B_1", alternatives=["A_to_B_2"], state="A",
    )
    sm.A_to_B_1()
    belief.update_internal(
        "decision", "test_agent", chosen="B_to_C", alternatives=[], state="B",
    )
    sm.B_to_C()
    return belief


def test_extract_decisions(belief_with_sm):
    viewer = StateMachineViewer(belief=belief_with_sm)
    decisions = viewer.extract_decisions()
    assert len(decisions) == 2
    assert decisions[0].step == 1
    assert decisions[0].state == "A"
    assert decisions[0].chosen == "A_to_B_1"
    assert decisions[0].alternatives == ["A_to_B_2"]
    assert decisions[1].step == 2
    assert decisions[1].chosen == "B_to_C"


def test_extract_graph(belief_with_sm):
    viewer = StateMachineViewer(belief=belief_with_sm)
    graph = viewer.extract_graph()
    assert set(graph["states"]) == {"A", "B", "C"}
    triggers = {t["trigger"] for t in graph["transitions"]}
    assert triggers == {"A_to_B_1", "A_to_B_2", "B_to_C"}


def test_extract_graph_no_state_machine():
    belief = Belief()
    viewer = StateMachineViewer(belief=belief)
    graph = viewer.extract_graph()
    assert graph["states"] == []
    assert graph["transitions"] == []


def test_render_html(belief_with_sm):
    viewer = StateMachineViewer(belief=belief_with_sm)
    html = viewer.render_html()
    assert "<!DOCTYPE html>" in html
    assert "Sherpa State Machine Viewer" in html
    assert ">A</text>" in html
    assert ">B</text>" in html
    assert ">C</text>" in html
    assert "A_to_B_1" in html
    assert "B_to_C" in html
    assert 'class="chosen"' in html
    assert "A_to_B_2" in html


def test_render_to_file(belief_with_sm, tmp_path):
    viewer = StateMachineViewer(belief=belief_with_sm)
    output = tmp_path / "test_viz.html"
    result_path = viewer.render(str(output))
    assert output.exists()
    assert output.stat().st_size > 0
    content = output.read_text()
    assert "Sherpa State Machine Viewer" in content


def test_render_empty_decisions():
    sm = SherpaStateMachine(states=["X", "Y"], initial="X")
    sm.update_transition("go", "X", "Y", action=EmptyAction())
    belief = Belief()
    belief.state_machine = sm
    viewer = StateMachineViewer(belief=belief)
    html = viewer.render_html()
    assert "No decisions recorded yet." in html
    assert ">X</text>" in html
    assert ">Y</text>" in html