from typing import List, Optional

from langchain.base_language import BaseLanguageModel
from loguru import logger

from sherpa_ai.action_planner import ActionPlanner
from sherpa_ai.actions import GoogleSearch, SynthesizeOutput
from sherpa_ai.actions.base import BaseAction
from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.config import AgentConfig
from sherpa_ai.events import EventType
from sherpa_ai.memory import Belief
from sherpa_ai.memory.shared_memory import SharedMemory
from sherpa_ai.output_parsers.base import BaseOutputProcessor
from sherpa_ai.output_parsers.citation_validation import CitationValidation
from sherpa_ai.output_parsers.number_validation import NumberValidation
from sherpa_ai.output_parsers.validation_result import ValidationResult
from sherpa_ai.verbose_loggers.verbose_loggers import DummyVerboseLogger

# TODO: QA Agent only contains partial implementation from the original
# task agent, more investigation is needed to add more content to it.
# Some of the feature may be added to the agent base class, such as
# the verbose logger.

ACTION_PLAN_DESCRIPTION = "Given your specialized expertise, historical context, and your mission to facilitate Machine-Learning-based solutions, determine which action and its corresponding arguments would be the most scientifically sound and efficient approach to achieve the described task."  # noqa: E501

TASK_AGENT_DESRIPTION = "You are a **question answering assistant** who solves user questions and offers a detailed solution."  # noqa: E501


class QAAgent(BaseAgent):
    """
    The task agent is the agent handles a single task.
    """

    def __init__(
        self,
        llm: BaseLanguageModel,
        name: str = "QA Agent",
        description: str = TASK_AGENT_DESRIPTION,
        shared_memory: SharedMemory = None,
        belief: Optional[Belief] = None,
        agent_config: AgentConfig = AgentConfig(),
        num_runs: int = 3,
        verbose_logger=DummyVerboseLogger(),
        require_meta=False,
        perform_number_validation=False,
        validation_count: int = 3,
        citation_thresh=[
            0.65,
            0.65,
            0.65,
        ],  # threshold for citations seq_thresh, jaccard_thresh, token_overlap,
        actions: List[BaseAction] = [],
        validation_steps: int = 1,
        validations: List[BaseOutputProcessor] = [],
    ):
        """
        The QA agent is the agent handles a single task.

        Args:
            llm (BaseLanguageModel): The language model used to generate text
            name (str, optional): The name of the agent. Defaults to "QA Agent".
            description (str, optional): The description of the agent. Defaults
                to TASK_AGENT_DESRIPTION.
            shared_memory (SharedMemory, optional): The shared memory used to
                store the context shared with all other agents. Defaults to None.
            belief (Belief, optional): The belief of the agent. Defaults to Belief().
            num_runs (int, optional): The number of runs the agent will run. Defaults
                to 3.
            verbose_logger (BaseVerboseLogger, optional): The verbose logger used to
                log the agent's internal state. Defaults to DummyVerboseLogger().
            require_meta (bool, optional): Whether the agent requires meta information
                during Google search. True means the search will use metadata and
                citation validation will be performed.
        """
        super().__init__(
            name,
            description + "\n\n" + f"Your name is {name}.",
            shared_memory,
            belief,
            ActionPlanner(description, ACTION_PLAN_DESCRIPTION, llm),
            num_runs,
            verbose_logger,
            actions,
            validation_steps,
            validations,
        )
        self.llm = llm
        self.require_meta = require_meta
        self.citation_thresh = citation_thresh
        self.config = agent_config
        self.validation_count = validation_count
        self.perform_number_validation = perform_number_validation

        if belief is None:
            belief = Belief()
        self.belief = belief

    def create_actions(self) -> List[BaseAction]:
        return [
            GoogleSearch(
                self.description,
                self.belief.current_task,
                self.llm,
                config=self.config,
                require_meta=self.require_meta,
            ),
        ]

    def synthesize_output(self) -> str:
        synthesize_action = SynthesizeOutput(
            self.description, self.llm, add_citation=self.require_meta
        )
        result = synthesize_action.execute(
            self.belief.current_task.content,
            self.belief.get_context(self.llm.get_num_tokens),
            self.belief.get_internal_history(self.llm.get_num_tokens),
        )

        # number_validation = self.num_validation(
        #     result=result, synthesize_action=synthesize_action
        # )
        # return number_validation
        return result

    def num_validation(self, result, synthesize_action) -> str:
        if not self.perform_number_validation and not self.require_meta:
            return result

        count = 0
        while count < self.validation_count:
            validation_result = self.process_output(result)

            if validation_result.is_valid or count == self.validation_count:
                result = validation_result.result
                break
            else:
                count += 1
                self.belief.update_internal(
                    EventType.feedback, "critic", validation_result.feedback
                )

            result = synthesize_action.execute(
                self.belief.current_task.content,
                self.belief.get_context(self.llm.get_num_tokens),
                self.belief.get_histories_excluding_types(
                    token_counter=self.llm.get_num_tokens,
                    exclude_type=[EventType.result],
                ),
            )

            # update intermidiate belief for round
            self.belief.update_internal(EventType.result, self.name, result)
            if count == self.validation_count:
                result = (
                    result
                    + "The numeric value results might not be fully reliable. Exercise caution and consider alternative sources if possible."
                )

        self.belief.update_internal(EventType.result, self.name, result)
        return result

    def process_output(self, generated: str) -> ValidationResult:
        if self.perform_number_validation:
            internal_history = self.belief.get_histories_excluding_types(
                token_counter=self.llm.get_num_tokens,
                exclude_type=[EventType.feedback, EventType.result],
            )
            num_val = NumberValidation(internal_history)
            result = num_val.process_output(generated)

        if self.require_meta:
            result = self.add_citation(generated)
        return result

    def add_citation(self, text) -> ValidationResult:
        google = None
        for action in self.belief.actions:
            if isinstance(action, GoogleSearch):
                google = action

        citation_module = CitationValidation(
            self.citation_thresh[0], self.citation_thresh[1], self.citation_thresh[2]
        )

        result = ValidationResult(
            is_valid=True,
            result=text,
            feedback="",
        )
        # only do citation validation if search was used
        if google is None or len(google.meta) == 0:
            return text

        resource = google.meta[-1]

        result = citation_module.parse_output(text, resource)

        return result
