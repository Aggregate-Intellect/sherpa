from typing import List

from langchain.base_language import BaseLanguageModel

from sherpa_ai.action_planner import ActionPlanner
from sherpa_ai.actions import Deliberation, GoogleSearch, SynthesizeOutput
from sherpa_ai.actions.arxiv_search import ArxivSearch
from sherpa_ai.actions.base import BaseAction
from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.memory import Belief, SharedMemory
from sherpa_ai.verbose_loggers.verbose_loggers import DummyVerboseLogger

ACTION_PLAN_DESCRIPTION = "Given your specialized expertise, historical context, and your mission to facilitate Machine-Learning-based solutions, determine which action and its corresponding arguments would be the most scientifically sound and efficient approach to achieve the described task."  # noqa: E501


ML_ENGINEER_DESCRIPTION = """You are a skilled machine learning engineer with a deep-rooted expertise in understanding and analyzing various Machine Learnng algorithm and use it to solve practical problems. \
Your primary role is to assist individuals, organizations, and researchers in using machine learning models to solve Machine-Learning-Related chalenges, \
using your knowledge to guide decisions and ensure the accuracy and reliability of outcomes.\
If you encounter a question or challenge outside your current knowledge base, you acknowledge your limitations and seek assistance or additional resources to fill the gaps. \
"""  # noqa: E501


class MLEngineer(BaseAgent):
    """
    The machine learning agent answers questions or research about ML-related topics
    """

    def __init__(
        self,
        llm: BaseLanguageModel,
        name="ML Engineer",
        description=ML_ENGINEER_DESCRIPTION,
        shared_memory: SharedMemory = None,
        num_runs=3,
        verbose_logger=DummyVerboseLogger(),
    ):
        self.llm = llm
        self.name = name
        self.description = description
        self.shared_memory = shared_memory
        self.action_planner = ActionPlanner(description, ACTION_PLAN_DESCRIPTION, llm)
        self.num_runs = num_runs
        self.belief = Belief()
        self.verbose_logger = verbose_logger

    def create_actions(self) -> List[BaseAction]:
        return [
            Deliberation(self.description, self.llm),
            GoogleSearch(self.description, self.belief.current_task, self.llm),
            ArxivSearch(self.description, self.belief.current_task, self.llm),
        ]

    def synthesize_output(self) -> str:
        synthesize_action = SynthesizeOutput(self.description, self.llm)
        result = synthesize_action.execute(
            self.belief.current_task.content,
            self.belief.get_context(self.llm.get_num_tokens),
            self.belief.get_internal_history(self.llm.get_num_tokens),
        )

        return result
