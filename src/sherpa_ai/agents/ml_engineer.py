from typing import List

from sherpa_ai.actions import Deliberation, GoogleSearch, SynthesizeOutput
from sherpa_ai.actions.arxiv_search import ArxivSearch
from sherpa_ai.actions.base import BaseAction
from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.memory import Belief
from sherpa_ai.policies import ReactPolicy

class MLEngineer(BaseAgent):
    """A specialized agent for answering questions about machine learning topics.

    This agent is designed to handle questions and research tasks related to machine
    learning, artificial intelligence, and data science. It can search for information
    from various sources and synthesize comprehensive responses.

    Attributes:
        name (str): The name of the agent, defaults to "ML Engineer".
        description (str): A description of the agent's purpose and capabilities.
        num_runs (int): Number of action execution cycles, defaults to 3.

    Example:
        >>> from sherpa_ai.agents.ml_engineer import MLEngineer
        >>> agent = MLEngineer(name="AI Researcher")
        >>> print(agent.name)
        AI Researcher
    """

    name: str = "ML Engineer"
    description: str = None
    num_runs: int = 3

    def __init__(self, *args, **kwargs):
        """Initialize an ML Engineer agent with appropriate configuration and policy.

        This method sets up the agent's description, policy, and belief system
        based on the provided arguments and template prompts.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Example:
            >>> from sherpa_ai.agents.ml_engineer import MLEngineer
            >>> agent = MLEngineer(name="AI Researcher")
            >>> print(agent.name)
            AI Researcher
        """
        super().__init__(*args, **kwargs)
        template = self.prompt_template
        self.description = template.format_prompt(
            prompt_parent_id="ml_engineer_prompts",
            prompt_id="ML_ENGINEER_DESCRIPTION",
            version="1.0",
        )
        action_planner= template.format_prompt(
            prompt_parent_id="ml_engineer_prompts",
            prompt_id="ACTION_PLAN_DESCRIPTION",
            version="1.0")
        if self.belief is None:
            self.belief = Belief()

        if self.policy is None:
            self.policy = ReactPolicy(
                role_description=self.description,
                output_instruction=action_planner,
                llm=self.llm,
            )

    def create_actions(self) -> List[BaseAction]:
        """Create and return the list of actions available to this agent.

        This method defines the specific actions that the ML Engineer agent can perform,
        including deliberation, Google search, and arXiv search for finding information.

        Returns:
            List[BaseAction]: List of action objects that the agent can use.

        Example:
            >>> from sherpa_ai.agents.ml_engineer import MLEngineer
            >>> agent = MLEngineer()
            >>> actions = agent.create_actions()
            >>> print(len(actions))
            3
            >>> print([action.__class__.__name__ for action in actions])
            ['Deliberation', 'GoogleSearch', 'ArxivSearch']
        """
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
        """Generate the final answer based on the agent's actions and belief state.

        This method creates a SynthesizeOutput action and executes it with the
        current task, context, and internal history to produce a coherent response.

        Returns:
            str: The synthesized answer to the machine learning question.

        Example:
            >>> from sherpa_ai.agents.ml_engineer import MLEngineer
            >>> agent = MLEngineer()
            >>> agent.belief.current_task.content = "Explain neural networks"
            >>> # In a real scenario, this would generate a response based on
            >>> # the agent's actions and belief state
            >>> # result = agent.synthesize_output()
            >>> # print(result)
        """
        synthesize_action = SynthesizeOutput(
            role_description=self.description, llm=self.llm
        )
        result = synthesize_action.execute(
            self.belief.current_task.content,
            self.belief.get_context(self.llm.get_num_tokens),
            self.belief.get_internal_history(self.llm.get_num_tokens),
        )

        return result
