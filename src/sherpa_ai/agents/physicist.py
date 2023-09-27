from sherpa_ai.agents.base import BaseAgent



physics_description = """You are a very smart physicist. \
You are great at answering questions about physics in a concise and easy to understand manner. \
When you don't know the answer to a question you admit that you don't know."""

class Physicist(BaseAgent):
    """
    The physicist agent answers questions or research about physics-related topics
    """
    def __init__(
        self,
        name = "physicist",
        description = physics_description,
    ):
        self.name = name
        self.description = description
