from typing import List

from loguru import logger

from sherpa_ai.actions.base import BaseAction
from sherpa_ai.agents.base import BaseAgent


class UserAgent(BaseAgent):
    """A specialized agent that redirects tasks to human users.

    This agent serves as a bridge between the AI system and human users,
    allowing tasks to be delegated to human experts when automated processing
    is not suitable or when human input is required.

    Attributes:
        name (str): The name of the agent, defaults to "User".
        description (str): A description of the agent's purpose, defaults to
            "A user agent that redirects the task to an expert".
        user_id (str): The identifier of the human user to redirect tasks to.
        verbose_logger (Any): Logger for displaying messages to the user.

    Example:
        >>> from sherpa_ai.agents.user import UserAgent
        >>> agent = UserAgent(user_id="expert1")
        >>> agent.belief.current_task.content = "Analyze this data"
        >>> result = agent.run()
        >>> print(result)
        @expert1 Please complete the following task: 
        Analyze this data
    """

    name: str = "User"
    description: str = "A user agent that redirects the task to an expert"

    def create_actions(self) -> List[BaseAction]:
        """Create an empty list of actions as this agent delegates to humans.

        Returns:
            List[BaseAction]: An empty list since this agent doesn't perform actions.

        Example:
            >>> from sherpa_ai.agents.user import UserAgent
            >>> agent = UserAgent()
            >>> actions = agent.create_actions()
            >>> print(len(actions))
            0
        """
        pass

    def synthesize_output(self) -> str:
        """Return an empty string as this agent doesn't synthesize output.

        Returns:
            str: An empty string.

        Example:
            >>> from sherpa_ai.agents.user import UserAgent
            >>> agent = UserAgent()
            >>> output = agent.synthesize_output()
            >>> print(output)
            
        """
        pass

    def run(
        self,
    ) -> str:
        """Redirect the task to a human user and return their response.

        This method displays the task to the human user and waits for their input.
        The user's response is then stored in the shared memory and returned.

        Returns:
            str: The human user's response to the task.

        Example:
            >>> from sherpa_ai.agents.user import UserAgent
            >>> agent = UserAgent(user_id="expert1")
            >>> agent.belief.current_task.content = "Review this code"
            >>> # In a real scenario, this would prompt the user and wait for input
            >>> # result = agent.run()
            >>> # print(result)
        """
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
