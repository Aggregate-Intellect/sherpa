from typing import List, Optional

from langchain_core.language_models import BaseLanguageModel 

from sherpa_ai.actions import Deliberation, GoogleSearch, SynthesizeOutput
from sherpa_ai.actions.arxiv_search import ArxivSearch
from sherpa_ai.actions.base import BaseAction
from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.memory import Belief, SharedMemory
from sherpa_ai.policies import ReactPolicy
from sherpa_ai.policies.base import BasePolicy
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
        policy: Optional[BasePolicy] = None,
        num_runs=3,
        verbose_logger=DummyVerboseLogger(),
    ):
        super().__init__(
            name=name,
            description=description,
            shared_memory=shared_memory,
            belief=Belief(),
            policy=policy,
            num_runs=num_runs,
            verbose_logger=verbose_logger,
        )

        if self.policy is None:
            self.policy = ReactPolicy(
                role_description=description,
                output_instruction=ACTION_PLAN_DESCRIPTION,
                llm=llm,
            )

        self.llm = llm

    def create_actions(self) -> List[BaseAction]:
        return [
            Deliberation(role_description=self.description, llm=self.llm),
            GoogleSearch(
                role_description=self.description,
                task=self.belief.current_task.content,
                llm=self.llm,
            ),
            ArxivSearch(
                role_description=self.description,
                task=self.belief.current_task.content,
                llm=self.llm,
            ),
        ]

    def synthesize_output(self) -> str:
        synthesize_action = SynthesizeOutput(
            role_description=self.description, llm=self.llm
        )
        result = synthesize_action.execute(
            self.belief.current_task.content,
            self.belief.get_context(self.llm.get_num_tokens),
            self.belief.get_internal_history(self.llm.get_num_tokens),
        )

        return result
