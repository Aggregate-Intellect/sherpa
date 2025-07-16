from actions import SearchAction
from langchain_core.language_models import BaseChatModel
from transitions.extensions import HierarchicalAsyncGraphMachine

from sherpa_ai.actions.base import BaseAction
from sherpa_ai.agents.qa_agent import QAAgent
from sherpa_ai.memory.belief import Belief
from sherpa_ai.memory.shared_memory import SharedMemory
from sherpa_ai.memory.state_machine import SherpaStateMachine


def get_actions(
    llm: BaseChatModel, belief: Belief, shared_memory: SharedMemory
) -> dict[str, BaseAction]:
    """Get the actions for the researcher agent."""
    search_action = SearchAction(
        belief=belief,
        shared_memory=shared_memory,
        llm=llm,
        name="search",
        args={"conversation_context": "Conversation context for search"},
        usage="An action that performs a search operation.",
    )
    return {
        "search": search_action,
    }


def create_state_machine(
    llm: BaseChatModel, belief: Belief, shared_memory: SharedMemory
):
    """Create a state machine for the researcher agent."""
    states = [{"name": "Searching", "tags": ["waiting"]}]

    transitions = [
        {
            "trigger": "perform_search",
            "source": "Searching",
            "dest": "Searching",
            "before": "search",
        },
    ]
    initial = "Searching"

    action_map = get_actions(llm, belief, shared_memory)
    sm = SherpaStateMachine(
        states=states,
        transitions=transitions,
        initial=initial,
        action_map=action_map,
        sm_cls=HierarchicalAsyncGraphMachine,
    )

    belief.state_machine = sm

    return belief


def get_researcher_agent(
    llm: BaseChatModel, shared_memory: SharedMemory, name: str = "Researcher"
) -> QAAgent:
    belief = Belief()
    """Get the researcher agent with its state machine and actions."""
    belief = create_state_machine(llm, belief, shared_memory)
    return QAAgent(name=name, belief=belief, llm=llm, num_runs=1)
