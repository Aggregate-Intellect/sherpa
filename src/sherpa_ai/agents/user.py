from typing import List

from loguru import logger

from sherpa_ai.actions.base import BaseAction
from sherpa_ai.agents.base import BaseAgent


class UserAgent(BaseAgent):
    """
    A wrapper class for redirecting the task to a real person
    """

    name: str = "User"
    description: str = "A user agent that redirects the task to an expert"

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

        if self.verbose_logger is None:
            logger.warning("No event logger provided. Using print instead.")
            print(message)
            result = input()
            self.shared_memory.add(event_type="result", name=self.name, content=result)
            return result
        else:
            self.verbose_logger.log(message)
            return result
