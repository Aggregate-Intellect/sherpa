from typing import List

from sherpa_ai.actions import Deliberation, GoogleSearch, SynthesizeOutput
from sherpa_ai.actions.base import BaseAction
from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.memory.belief import Belief
from sherpa_ai.policies import ReactPolicy

class Physicist(BaseAgent):
    """A specialized agent for answering questions about physics topics.

    This agent is designed to handle questions and research tasks related to physics,
    including classical mechanics, quantum mechanics, relativity, and other physical
    theories. It can search for information and synthesize comprehensive responses.

    Attributes:
        name (str): The name of the agent, defaults to "Physicist".
        description (str): A description of the agent's purpose and capabilities.
        num_runs (int): Number of action execution cycles, defaults to 3.

    Example:
        >>> from sherpa_ai.agents.physicist import Physicist
        >>> agent = Physicist(name="Quantum Expert")
        >>> print(agent.name)
        Quantum Expert
    """


    name: str = "Physicist"
    description: str = None
    num_runs: int = 3

    def __init__(self, *args, **kwargs):
        """Initialize a Physicist agent with appropriate configuration and policy.

        This method sets up the agent's description, policy, and belief system
        based on the provided arguments and template prompts.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Example:
            >>> from sherpa_ai.agents.physicist import Physicist
            >>> agent = Physicist(name="Quantum Expert")
            >>> print(agent.name)
            Quantum Expert
        """
        super().__init__(*args, **kwargs)
        template = self.prompt_template
        action_planner = template.format_prompt(
            prompt_parent_id="physicist_prompts",
            prompt_id="ACTION_PLAN_DESCRIPTION",
            version="1.0",
        )
        self.description = template.format_prompt(
            prompt_parent_id="physicist_prompts",
            prompt_id="PHYSICIST_DESCRIPTION",
            version="1.0",
    )

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

        This method defines the specific actions that the Physicist agent can perform,
        including deliberation and Google search for finding information.

        Returns:
            List[BaseAction]: List of action objects that the agent can use.

        Example:
            >>> from sherpa_ai.agents.physicist import Physicist
            >>> agent = Physicist()
            >>> actions = agent.create_actions()
            >>> print(len(actions))
            2
            >>> print([action.__class__.__name__ for action in actions])
            ['Deliberation', 'GoogleSearch']
        """
        return [
            Deliberation(role_description=self.description, llm=self.llm),
            GoogleSearch(
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
            str: The synthesized answer to the physics question.

        Example:
            >>> from sherpa_ai.agents.physicist import Physicist
            >>> agent = Physicist()
            >>> agent.belief.current_task.content = "Explain quantum entanglement"
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
