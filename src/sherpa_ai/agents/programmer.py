from sherpa_ai.agents.base import BaseAgent


class Programmer(BaseAgent):
    """
    The programmer receives requirements about a program and write it
    """
    def __init__(self):
        self.description = "The programmer receives requirements about a program and write it"
