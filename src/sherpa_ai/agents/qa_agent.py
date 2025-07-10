from typing import List, Optional

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
    """A specialized agent for answering questions and providing information.

    This agent is designed to handle question-answering tasks by searching for
    information, synthesizing responses, and validating outputs. It can optionally
    include citations in its responses.

    Attributes:
        name (str): The name of the agent, defaults to "QA Agent".
        description (str): A description of the agent's purpose and capabilities.
        config (AgentConfig): Configuration settings for the agent.
        num_runs (int): Number of action execution cycles, defaults to 3.
        global_regen_max (int): Maximum number of output regeneration attempts, defaults to 5.
        citation_enabled (bool): Whether to include citations in responses, defaults to False.

    Args:
        custom_task_description_prompt (Optional[str]): Custom prompt for task description. If None, uses default from prompt template.
        custom_action_plan_prompt (Optional[str]): Custom prompt for action plan description. If None, uses default from prompt template.

    Example:
        >>> from sherpa_ai.agents.qa_agent import QAAgent
        >>> from sherpa_ai.config import AgentConfig
        >>> agent = QAAgent(
        ...     name="Research Assistant",
        ...     config=AgentConfig(),
        ...     citation_enabled=True
        ... )
        >>> print(agent.name)
        Research Assistant
        >>> # Using custom prompts
        >>> agent = QAAgent(
        ...     name="Custom QA",
        ...     custom_task_description_prompt="You are an expert QA assistant.",
        ...     custom_action_plan_prompt="Plan to solve: {task}"
        ... )
        >>> print(agent.description)
        You are an expert QA assistant.\n\nYour name is Custom QA.
    """  # noqa: E501

    name: str = "QA Agent"
    description: str = None
    config: AgentConfig = None
    num_runs: int = 3
    global_regen_max: int = 5
    citation_enabled: bool = False

    def __init__(
        self,
        *args,
        custom_task_description_prompt: Optional[str] = None,
        custom_action_plan_prompt: Optional[str] = None,
        **kwargs
    ):
        """Initialize a QA agent with appropriate configuration and policy.

        Sets up the agent's description, policy, and belief system using provided
        custom prompts or default template prompts from prompts.json.

        Args:
            *args: Variable length argument list.
            custom_task_description_prompt (Optional[str]): Custom prompt for task description.
            custom_action_plan_prompt (Optional[str]): Custom prompt for action plan description.
            **kwargs: Arbitrary keyword arguments.

        Example:
            >>> from sherpa_ai.agents.qa_agent import QAAgent
            >>> agent = QAAgent(name="Research Assistant")
            >>> print(agent.name)
            Research Assistant
            >>> # With custom prompt
            >>> agent = QAAgent(
            ...     name="Custom QA",
            ...     custom_task_description_prompt="Expert QA for all queries."
            ... )
            >>> print(agent.description)
            Expert QA for all queries.\n\nYour name is Custom QA.
        """
        super().__init__(*args, **kwargs)

        if custom_task_description_prompt is not None:
            self.description = custom_task_description_prompt
        else:
            template = self.prompt_template
            self.description = template.format_prompt(
                prompt_parent_id="qa_agent_prompts",
                prompt_id="TASK_AGENT_DESCRIPTION",
                version="1.0",
            )

        if custom_action_plan_prompt is not None:
            action_planner = custom_action_plan_prompt
        else:
            template = self.prompt_template
            action_planner = template.format_prompt(
                prompt_parent_id="qa_agent_prompts",
                prompt_id="ACTION_PLAN_DESCRIPTION",
                version="1.0",
            )

        self.description = self.description + "\n\n" + f"Your name is {self.name}."

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
        """Create and return the list of actions available to this agent.

        This method defines the specific actions that the QA agent can perform,
        including Google search for finding information.

        Returns:
            List[BaseAction]: List of action objects that the agent can use.

        Example:
            >>> from sherpa_ai.agents.qa_agent import QAAgent
            >>> agent = QAAgent()
            >>> actions = agent.create_actions()
            >>> print(len(actions))
            1
            >>> print(actions[0].__class__.__name__)
            GoogleSearch
        """
        return [
            GoogleSearch(
                role_description=self.description,
                task=self.belief.current_task.content
                if self.belief.current_task
                else "",
                llm=self.llm,
                config=self.config,
                belief=self.belief,
            ),
        ]

    def synthesize_output(self) -> str:
        """Generate the final answer based on the agent's actions and belief state.

        This method creates a SynthesizeOutput action and executes it with the
        current task, context, and internal history to produce a coherent response.

        Returns:
            str: The synthesized answer to the question.

        Example:
            >>> from sherpa_ai.agents.qa_agent import QAAgent
            >>> agent = QAAgent()
            >>> agent.belief.current_task.content = "What is machine learning?"
            >>> # In a real scenario, this would generate a response based on
            >>> # the agent's actions and belief state
            >>> # result = agent.synthesize_output()
            >>> # print(result)
        """
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
