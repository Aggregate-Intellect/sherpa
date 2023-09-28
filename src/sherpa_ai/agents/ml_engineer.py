from sherpa_ai.agents.base import BaseAgent

ml_engineer_description = """You are a skilled machine learning engineer. \
Your expertise lies in developing and implementing machine learning models to solve complex problems. \
You can answers questions or research about ML-related topics. \
If you encounter a question or challenge outside your current knowledge base, you acknowledge your limitations and seek assistance or additional resources to fill the gaps. \
"""


class MLEngineer(BaseAgent):
    """
    The ML engineer answers questions or research about ML-related topics
    """

    def __init__(
        self,
        name="machine learning engineer",
        description=ml_engineer_description,
    ):
        self.name = name
        self.description = description

    # TODO: Name, description, actions (Arxiv search, huggingface, Create output)
    # Prompt to select actions
