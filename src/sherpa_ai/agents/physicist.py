from typing import List, Optional

from langchain_core.language_models import BaseLanguageModel 

from sherpa_ai.actions import Deliberation, GoogleSearch, SynthesizeOutput
from sherpa_ai.actions.base import BaseAction
from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.memory import Belief, SharedMemory
from sherpa_ai.policies import ReactPolicy
from sherpa_ai.policies.base import BasePolicy
from sherpa_ai.verbose_loggers.verbose_loggers import DummyVerboseLogger


PHYSICIST_DESCRIPTION = "You are a physicist with a deep-rooted expertise in understanding and analyzing the fundamental principles of the universe, spanning from the tiniest subatomic particles to vast cosmic phenomena. Your primary role is to assist individuals, organizations, and researchers in navigating and resolving complex physics-related challenges, using your knowledge to guide decisions and ensure the accuracy and reliability of outcomes."  # noqa: E501

ACTION_PLAN_DESCRIPTION = "Given your specialized expertise, historical context, and your mission to facilitate physics-based solutions, determine which action and its corresponding arguments would be the most scientifically sound and efficient approach to achieve the described task."  # noqa: E501


class Physicist(BaseAgent):
    """
    The physicist agent answers questions or research about physics-related topics
    """

    def __init__(
        self,
        llm: BaseLanguageModel,
        name="Physicist",
        description=PHYSICIST_DESCRIPTION,
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
