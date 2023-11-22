import pytest
from langchain.chat_models import ChatOpenAI

from sherpa_ai.agents import Physicist
from sherpa_ai.events import Event
from sherpa_ai.orchestrator import EventType, Orchestrator, OrchestratorConfig
from tests.fixtures.llms import get_llm


@pytest.mark.external_api
def test_orchestrator_successful(get_llm):
    orchestrator = Orchestrator(OrchestratorConfig())
    llm = get_llm(__file__, test_orchestrator_successful.__name__)

    orchestrator.shared_memory.add_event(
        Event(event_type=EventType.task, agent="shared_memory", content="shared_memory")
    )

    physicist = Physicist(llm=llm, shared_memory=orchestrator.shared_memory)
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
