from sherpa_ai.agents.base import BaseAgent


class Physicist(BaseAgent):
    """
    The physicist agent answers questions or research about physics-related topics
    """
    def __init__(
        self,
        name: str,
        description: str,
    ):
        self.name = name
        self.description = description
