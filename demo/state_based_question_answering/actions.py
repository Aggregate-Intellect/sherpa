
from sherpa_ai.actions.base import BaseAction
from sherpa_ai.events import Event, EventType
from sherpa_ai.memory.belief import Belief


class UserHelp(BaseAction):
    args: dict = {"question": "str"}

    def execute(self, question: str) -> str:
        clarification = input(question)

        return clarification


class Respond(BaseAction):
    args: dict = {"response": "str"}

    def execute(self, response: str) -> str:
        print(response)

        return "success"


class StartQuestion(BaseAction):
    belief: Belief
    args: dict = {}

    def execute(self) -> str:
        question = input()
        self.belief.set_current_task(Event(EventType.task, "user", question))

        return "success"
