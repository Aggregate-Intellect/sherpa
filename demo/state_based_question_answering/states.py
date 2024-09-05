from actions import Respond, StartQuestion, UserHelp
from transitions.extensions import (GraphMachine, HierarchicalGraphMachine,
                                    HierarchicalMachine)

from sherpa_ai.actions.base import BaseAction
from sherpa_ai.actions.belief_actions import RetrieveBelief, UpdateBelief
from sherpa_ai.memory.belief import Belief
from sherpa_ai.memory.state_machine import SherpaStateMachine


def get_actions(belief: Belief) -> dict[str, BaseAction]:
    start_question = StartQuestion(
        name="start_question",
        usage="Start the question answering process",
        belief=belief,
    )

    clarify_question = UserHelp(
        name="clarify_question",
        usage="Ask questions to clarify the intention of user",
        belief=belief,
    )
    answer_question = Respond(
        name="answer_question",
        usage="Answer the user's question based on the current context",
        belief=belief,
    )

    update_belief = UpdateBelief(belief=belief)

    retrieve_belief = RetrieveBelief(belief=belief)

    actions = [
        start_question,
        clarify_question,
        answer_question,
        update_belief,
        retrieve_belief,
    ]

    return {action.name: action for action in actions}


def add_qa_sm(belief: Belief) -> Belief:
    # states = [
    #     "Start",
    #     {"name": "Waiting", "on_enter": "start_question"},
    #     "QA",
    #     "Clarification",
    # ]
    # initial = "Start"

    # transitions = [
    #     {
    #         "trigger": "start",
    #         "source": "Start",
    #         "dest": "Waiting",
    #     },
    #     {"trigger": "Start_question_answering", "source": "Waiting", "dest": "QA"},
    #     {
    #         "trigger": "Ask_for_clarification",
    #         "source": "QA",
    #         "dest": "Clarification",
    #         "before": "clarify_question",
    #     },
    #     {
    #         "trigger": "Ask_for_clarification",
    #         "source": "Clarification",
    #         "dest": "Clarification",
    #         "before": "clarify_question",
    #     },
    #     {
    #         "trigger": "Update_belief",
    #         "source": "Clarification",
    #         "dest": "Clarification",
    #         "before": "update_belief",
    #     },
    #     {
    #         "trigger": "Retrieve_belief",
    #         "source": "Clarification",
    #         "dest": "Clarification",
    #         "before": "retrieve_belief",
    #     },
    #     {"trigger": "Finish_clarification", "source": "Clarification", "dest": "QA"},
    #     {
    #         "trigger": "Answer_question",
    #         "source": "QA",
    #         "dest": "Waiting",
    #         "before": "answer_question",
    #     },
    # ]

    states = [
        "Start",
        {"name": "Waiting", "on_enter": "start_question"},
        {
            "name": "QA",
            "children": ["Thinking", "Clarification", "Clarified"],
            "initial": "Thinking",
        },
    ]
    initial = "Start"

    transitions = [
        {
            "trigger": "start",
            "source": "Start",
            "dest": "Waiting",
        },
        {"trigger": "Start_question_answering", "source": "Waiting", "dest": "QA"},
        {
            "trigger": "Ask_for_clarification",
            "source": "QA_Thinking",
            "dest": "QA_Clarification",
        },
        {
            "trigger": "Ask_for_clarification",
            "source": "QA_Clarification",
            "dest": "QA_Clarified",
            "before": "clarify_question",
        },
        {
            "trigger": "Update_belief",
            "source": "QA_Clarified",
            "dest": "QA_Clarification",
            "before": "update_belief",
        },
        {
            "trigger": "Retrieve_belief",
            "source": "QA",
            "dest": "QA",
            "before": "retrieve_belief",
        },
        {
            "trigger": "Finish_clarification",
            "source": "QA_Clarification",
            "dest": "QA_Thinking",
        },
        {
            "trigger": "Answer_question",
            "source": "QA_Thinking",
            "dest": "Waiting",
            "before": "answer_question",
        },
    ]

    action_map = get_actions(belief)

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
