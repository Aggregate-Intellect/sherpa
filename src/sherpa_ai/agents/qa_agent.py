from typing import List

from sherpa_ai.actions import GoogleSearch, SynthesizeOutput
from sherpa_ai.actions.base import BaseAction
from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.config import AgentConfig
from sherpa_ai.memory import Belief
from sherpa_ai.output_parsers.citation_validation import CitationValidation
from sherpa_ai.policies import ReactPolicy

# TODO: QA Agent only contains partial implementation from the original
# task agent, more investigation is needed to add more content to it.
# Some of the feature may be added to the agent base class, such as
# the verbose logger.


class QAAgent(BaseAgent):
    """
    The task agent is the agent handles a single task.

    Attributes:
        llm (BaseLanguageModel): The language model used to generate text
        name (str, optional): The name of the agent. Defaults to "QA Agent".
        description (str, optional): The description of the agent. Defaults to
            TASK_AGENT_DESCRIPTION.
        shared_memory (SharedMemory, optional): The shared memory used to store
            information and shared with other agents. Defaults to None.
        belief (Optional[Belief], optional): The belief of the agent. Defaults to None.
        agent_config (AgentConfig, optional): The agent configuration. Defaults to
            AgentConfig.
        num_runs (int, optional): The number of runs the agent will perform. Defaults
            to 3.
        verbose_logger (BaseVerboseLogger, optional): The verbose logger used to log
            information. Defaults to DummyVerboseLogger().
        actions (List[BaseAction], optional): The list of actions the agent can perform.
            Defaults to [].
        validation_steps (int, optional): The number of validation steps the agent will
            perform. Defaults to 1.
        validations (List[BaseOutputProcessor], optional): The list of validations the
            agent will perform. Defaults to [].
    """

    name: str = "QA Agent"
    description: str = None
    config: AgentConfig = None
    num_runs: int = 3
    global_regen_max: int = 5
    citation_enabled: bool = False

    def __init__(self, *args, **kwargs):
        """
        The QA agent handles a single question-answering task.

        Args:

        """
        super().__init__(*args, **kwargs)
        template = self.prompt_template
        self.description = template.format_prompt(
            wrapper="qa_agent_prompts",
            name="TASK_AGENT_DESCRIPTION",
            version="1.0",
        )

        self.description = self.description + "\n\n" + f"Your name is {self.name}."

        action_planner = template.format_prompt(
            wrapper="qa_agent_prompts",
            name="ACTION_PLAN_DESCRIPTION",
            version="1.0",
        )

        if self.policy is None:
            self.policy = ReactPolicy(
                role_description=self.description,
                output_instruction=action_planner,
                llm=self.llm,
            )

        if self.config is None:
            self.config = AgentConfig()

        if self.belief is None:
            self.belief = Belief()

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
                belief=self.belief,
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
