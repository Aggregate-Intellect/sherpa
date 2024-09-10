
from sherpa_ai.actions.base import BaseAction
from sherpa_ai.events import Event, EventType
from sherpa_ai.memory.belief import Belief


class UserHelp(BaseAction):
    """
    Ask the user for clarification on a question.
    """
    args: dict = {"question": "str"}

    def execute(self, question: str) -> str:
        clarification = input(question)

        return clarification


class Respond(BaseAction):
    """
    Respond to the user with a message.
    """
    args: dict = {"response": "str"}

    def execute(self, response: str) -> str:
        print(response)

        return "success"


class StartQuestion(BaseAction):
    """
    Waiting the user to ask a question.
    """
    belief: Belief
    args: dict = {}

    def execute(self) -> str:
        question = input()
        self.belief.set_current_task(Event(EventType.task, "user", question))

        return "success"
