from unittest.mock import MagicMock

from sherpa_ai.agents import Physicist
from sherpa_ai.events import Event
from sherpa_ai.orchestrator import EventType, Orchestrator, OrchestratorConfig


def test_serialization_succeeds():
    orchestrator = Orchestrator(OrchestratorConfig())

    orchestrator.shared_memory.add_event(
        Event(event_type=EventType.task, agent="shared_memory", content="shared_memory")
    )

    physicist = Physicist(llm=MagicMock(), shared_memory=orchestrator.shared_memory)
    physicist.belief.update_internal(
        event_type=EventType.task, agent="belief", content="belief"
    )
    orchestrator.add_agent(physicist)

    dt = orchestrator.save(orchestrator.shared_memory, agents=[physicist])

    new_or = Orchestrator.restore(dt, orchestrator.agent_pool)
    assert (
        new_or.shared_memory.get_by_type(EventType.task)[0].content == "shared_memory"
    )

    new_physicist = new_or.agent_pool.agents[physicist.name]
    assert new_physicist.belief.get_by_type(EventType.task)[0].content == "belief"
