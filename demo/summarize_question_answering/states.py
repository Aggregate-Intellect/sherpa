from transitions.extensions import HierarchicalGraphMachine

from sherpa_ai.actions.base import BaseAction
from sherpa_ai.memory.belief import Belief
from sherpa_ai.memory.state_machine import SherpaStateMachine


def add_qa_sm(belief: Belief, action_map: dict[str, BaseAction]) -> Belief:
    # Hierarchical version of the state machine
    states = [
        "Start",
        {"name": "Waiting", "on_enter": "start_qa"},
        "Gathering",
        "Summarizing",
        "Finish"
    ]
    initial = "Start"

    transitions = [
        {
            "trigger": "start",
            "source": "Start",
            "dest": "Waiting",
        },
        {
            "trigger": "start_question_answering",
            "source": "Waiting",
            "dest": "Gathering",
        },
        {
            "trigger": "query_document",
            "source": "Gathering",
            "dest": "Gathering",
            "before": "query_document",
        },
        {
            "trigger": "summarize_answers",
            "source": "Gathering",
            "dest": "Summarizing",
            "conditions": "is_finished",
        },
        {
            "trigger": "answer_the_question",
            "source": "Summarizing",
            "dest": "Finish",
            "before": "answer_question",
        },
    ]

    sm = SherpaStateMachine(
        states=states,
        transitions=transitions,
        initial=initial,
        action_map=action_map,
        sm_cls=HierarchicalGraphMachine,
    )

    print(sm.sm.get_graph().draw(None))

    belief.state_machine = sm

    return belief
