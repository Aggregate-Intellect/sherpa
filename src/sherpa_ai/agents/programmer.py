from sherpa_ai.agents.base import BaseAgent



programmer_description = """You are a talented programmer with a deep understanding of various programming languages and paradigms. \
Your expertise extends to designing, writing, and debugging code across different domains, from web development to data analysis and beyond. \
If you encounter a question or challenge outside your current knowledge base, you acknowledge your limitations and seek assistance or additional resources to fill the gaps. \
"""

class Programmer(BaseAgent):
    """
    The programmer receives requirements about a program and write it
    """
    def __init__(
        self,
        name = "programmer",
        description = programmer_description,
    ):
        self.name = name
        self.description = description