from typing import List, Optional

from langchain_core.language_models import BaseLanguageModel 

from sherpa_ai.actions import GoogleSearch, SynthesizeOutput
from sherpa_ai.actions.base import BaseAction
from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.config import AgentConfig
from sherpa_ai.memory import Belief
from sherpa_ai.memory.shared_memory import SharedMemory
from sherpa_ai.output_parsers.base import BaseOutputProcessor
from sherpa_ai.output_parsers.citation_validation import CitationValidation
from sherpa_ai.policies import ReactPolicy
from sherpa_ai.policies.base import BasePolicy
from sherpa_ai.verbose_loggers.base import BaseVerboseLogger
from sherpa_ai.verbose_loggers.verbose_loggers import DummyVerboseLogger


# TODO: QA Agent only contains partial implementation from the original
# task agent, more investigation is needed to add more content to it.
# Some of the feature may be added to the agent base class, such as
# the verbose logger.

ACTION_PLAN_DESCRIPTION = "Given your specialized expertise, historical context, and your mission to facilitate Machine-Learning-based solutions, determine which action and its corresponding arguments would be the most scientifically sound and efficient approach to achieve the described task."  # noqa: E501

TASK_AGENT_DESCRIPTION = "You are a **question answering assistant** who solves user questions and offers a detailed solution."  # noqa: E501


class QAAgent(BaseAgent):
    """
    The task agent is the agent handles a single task.
    """

    def __init__(
        self,
        llm: BaseLanguageModel,
        name: str = "QA Agent",
        description: str = TASK_AGENT_DESCRIPTION,
        shared_memory: SharedMemory = None,
        belief: Optional[Belief] = None,
        agent_config: AgentConfig = AgentConfig(),
        policy: Optional[BasePolicy] = None,
        num_runs: int = 3,
        verbose_logger: BaseVerboseLogger = DummyVerboseLogger(),
        actions: List[BaseAction] = [],
        validation_steps: int = 1,
        validations: List[BaseOutputProcessor] = [],
        global_regen_max: int = 5,
    ):
        """
        The QA agent handles a single question-answering task.

        Args:
            llm (BaseLanguageModel): The language model used to generate text
            name (str, optional): The name of the agent. Defaults to "QA Agent".
            description (str, optional): The description of the agent. Defaults to TASK_AGENT_DESCRIPTION.
            shared_memory (SharedMemory, optional): The shared memory used to store information and shared with other agents. Defaults to None.
            belief (Optional[Belief], optional): The belief of the agent. Defaults to None.
            agent_config (AgentConfig, optional): The agent configuration. Defaults to AgentConfig.
            num_runs (int, optional): The number of runs the agent will perform. Defaults to 3.
            verbose_logger (BaseVerboseLogger, optional): The verbose logger used to log information. Defaults to DummyVerboseLogger().
            actions (List[BaseAction], optional): The list of actions the agent can perform. Defaults to [].
            validation_steps (int, optional): The number of validation steps the agent will perform. Defaults to 1.
            validations (List[BaseOutputProcessor], optional): The list of validations the agent will perform. Defaults to [].
        """
        super().__init__(
            llm=llm,
            name=name,
            description=description + "\n\n" + f"Your name is {name}.",
            shared_memory=shared_memory,
            belief=belief,
            policy=policy,
            num_runs=num_runs,
            verbose_logger=verbose_logger,
            actions=actions,
            validation_steps=validation_steps,
            validations=validations,
            global_regen_max=global_regen_max,
        )

        if self.policy is None:
            self.policy = ReactPolicy(
                role_description=description,
                output_instruction=ACTION_PLAN_DESCRIPTION,
                llm=llm,
            )

        self.llm = llm
        self.config = agent_config

        if belief is None:
            belief = Belief()
        self.belief = belief
        self.citation_enabled = False

        for validation in self.validations:
            if isinstance(validation, CitationValidation):
                self.citation_enabled = True
                break

    def create_actions(self) -> List[BaseAction]:
        return [
            GoogleSearch(
                role_description=self.description,
                task=self.belief.current_task.content,
                llm=self.llm,
                config=self.config,
            ),
        ]

    def synthesize_output(self) -> str:
        synthesize_action = SynthesizeOutput(
            role_description=self.description,
            llm=self.llm,
            add_citation=self.citation_enabled,
        )
        result = synthesize_action.execute(
            self.belief.current_task.content,
            self.belief.get_context(self.llm.get_num_tokens),
            self.belief.get_internal_history(self.llm.get_num_tokens),
        )
        return result
