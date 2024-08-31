from actions import Respond, StartQuestion, UserHelp

from sherpa_ai.actions.belief_actions import RetrieveBelief, UpdateBelief
from sherpa_ai.memory.belief import Belief
from sherpa_ai.memory.state_machine import SherpaStateMachine


def add_qa_sm(belief: Belief) -> Belief:
    sm = SherpaStateMachine(
        states=["Start", "Waiting", "QA", "Clarification"], initial="Start"
    )

    update_belief = StartQuestion(
        name="Update Belief",
        usage="Start the question answering process",
        belief=belief,
    )
    sm.add_state("Waiting", on_enter=update_belief)

    sm.add_transition("start", "Start", "Waiting")

    clarify_question = UserHelp(
        name="Ask_Clarify_Question",
        usage="Ask questions to clarify the intention of user",
        belief=belief,
    )
    answer_question = Respond(
        name="Answer_Question",
        usage="Answer the user's question based on the current context",
        belief=belief,
    )

    update_belief = UpdateBelief(belief=belief)

    retrieve_belief = RetrieveBelief(belief=belief)

    sm.add_transition("Start_question_answering", "Waiting", "QA")
    sm.add_transition(
        "Ask_for_clarification", "QA", "Clarification", action=clarify_question
    )
    sm.add_transition(
        "Ask_for_clarification",
        "Clarification",
        "Clarification",
        action=clarify_question,
    )

    sm.add_transition(
        "Update_belief", "Clarification", "Clarification", action=update_belief
    )

    sm.add_transition(
        "Retrieve_belief", "Clarification", "Clarification", action=retrieve_belief
    )

    sm.add_transition("Finish_clarification", "Clarification", "QA")
    sm.add_transition("Answer_question", "QA", "Waiting", action=answer_question)

    belief.state_machine = sm

    return belief
