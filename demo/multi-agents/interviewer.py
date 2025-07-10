from actions import QuestionAction, SummarizeAction
from langchain_core.language_models import BaseChatModel
from transitions.extensions import HierarchicalAsyncGraphMachine

from sherpa_ai.agents import QAAgent
from sherpa_ai.memory import Belief, SharedMemory
from sherpa_ai.memory.state_machine import SherpaStateMachine


def get_actions(llm: BaseChatModel, belief: Belief, shared_memory: SharedMemory):
    """Get the actions for the interviewer agent."""
    question_action = QuestionAction(
        llm=llm, belief=belief, shared_memory=shared_memory
    )
    summarize_action = SummarizeAction(llm=llm, belief=belief)
    return {
        "question": question_action,
        "summarize": summarize_action,
        "should_continue": question_action.should_continue,
    }


def create_state_machine(
    llm: BaseChatModel, belief: Belief, shared_memory: SharedMemory
):
    states = ["Start", {"name": "Gathering", "tags": ["waiting"]}, "Finish"]

    transitions = [
        {
            "trigger": "ask_question",
            "source": "Start",
            "dest": "Gathering",
            "before": "question",
        },
        {
            "trigger": "ask_question",
            "source": "Gathering",
            "dest": "Gathering",
            "before": "question",
            "conditions": "should_continue",
        },
        {
            "trigger": "summarize",
            "source": "Gathering",
            "dest": "Finish",
            "before": "summarize",
            "unless": "should_continue",
        },
    ]
    initial = "Start"

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


def get_interviewer_agent(
    llm: BaseChatModel, shared_memory: SharedMemory, name: str = "Interviewer"
) -> QAAgent:
    """Create an interviewer agent."""
    belief = Belief()
    create_state_machine(llm, belief, shared_memory)
    agent = QAAgent(name=name, belief=belief, llm=llm)
    return agent
