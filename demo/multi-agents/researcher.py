from typing import List

from sherpa_ai.actions.base import BaseAction
from sherpa_ai.agents.base import BaseAgent


class Researcher(BaseAgent):
    """An agent that conducts interviews with other agents."""

    def __init__(self, name: str = "Researcher", **kwargs):
        """Initialize the Researcher agent. Also initialize the state machine of the Researcher agent.

        Args:
            name (str): The name of the agent.
            **kwargs: Additional keyword arguments.
        """  # noqa: E501
        super().__init__(name=name, **kwargs)

    def create_actions(self) -> List[BaseAction]:
        """Create actions for the Researcher agent.

        This method is called to define the actions that the agent can perform.
        For the Researcher, it might include asking questions, recording answers,
        and summarizing responses.

        Returns:
            list: A list of actions that the agent can perform.
        """
        pass

    def synthesize_output(self) -> str:
        pass
