from typing import List

from loguru import logger

from sherpa_ai.actions.base import BaseAction
from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.events import EventType
from sherpa_ai.memory import Belief, SharedMemory


class UserAgent(BaseAgent):
    """
    A wrapper class for redirecting the task to a real person
    """

    def __init__(
        self,
        name: str,
        description: str,
        shared_memory: SharedMemory = None,
        user_id: str = None,
        event_logger=None,
    ):
        self.name = name
        self.description = description
        self.shared_memory = shared_memory
        self.user_id = user_id
        self.belief = Belief()
        self.event_logger = event_logger

    def create_actions(self) -> List[BaseAction]:
        pass

    def synthesize_output(self) -> str:
        pass

    def run(
        self,
    ) -> str:
        """
        Redirect the task to a real person
        """
        self.shared_memory.observe(self.belief)

        task = self.belief.current_task
        user_name = self.user_id if self.user_id else self.name
        message = f"@{user_name} Please complete the following task: \n{task.content}"

        if self.event_logger is None:
            logger.warning("No event logger provided. Using print instead.")
            print(message)
            result = input()
            self.shared_memory.add(
                event_type=EventType.result, agent=self.name, content=result
            )
            return result
        else:
            self.event_logger.log(message)
            return result
