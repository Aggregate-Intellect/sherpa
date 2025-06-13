"""ReAct framework policy implementation for Sherpa AI.

This module provides a policy implementation based on the ReAct framework
(https://arxiv.org/abs/2210.03629). It defines the ReactPolicy class which
selects actions by reasoning about the current state and available actions.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Optional

from loguru import logger
from pydantic import BaseModel, ConfigDict
from langchain_core.language_models.base import BaseLanguageModel

from sherpa_ai.policies.base import BasePolicy, PolicyOutput
from sherpa_ai.policies.exceptions import SherpaPolicyException
from sherpa_ai.policies.utils import is_selection_trivial, transform_json_output
from sherpa_ai.prompts.prompt_template_loader import PromptTemplate

if TYPE_CHECKING:
    from sherpa_ai.memory.belief import Belief


class ReactPolicy(BasePolicy):
    """Policy implementation based on the ReAct framework.

    This class implements action selection based on the ReAct framework,
    which combines reasoning and acting. It uses a language model to analyze
    the current state and available actions to select the most appropriate
    next action.

    Attributes:
        role_description (str): Description of agent role for action selection.
        output_instruction (str): Instruction for JSON output format.
        llm (Any): Language model for generating text (BaseLanguageModel).
        prompt_template (PromptTemplate): Template for generating prompts.
        response_format (dict): Expected JSON format for responses.
        model_config (ConfigDict): Configuration allowing arbitrary types.

    Example:
        >>> policy = ReactPolicy(
        ...     role_description="Assistant that helps with coding",
        ...     output_instruction="Choose the best action",
        ...     llm=language_model
        ... )
        >>> output = policy.select_action(belief)
        >>> print(output.action.name)
        'SearchCode'
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    role_description: str
    output_instruction: str
    llm: Optional[BaseLanguageModel] = None
    prompt_template: PromptTemplate = PromptTemplate("./sherpa_ai/prompts/prompts.json")
    response_format: dict = {
        "command": {
            "name": "tool/command name you choose",
            "args": {"arg name": "value"},
        },
    }

    async def async_select_action(self, belief: Belief) -> Optional[PolicyOutput]:
        """Asynchronously select an action based on current belief state.

        This method currently just calls the synchronous version. It exists
        to provide an async interface for future async implementations.

        Args:
            belief (Belief): Current belief state of the agent.

        Returns:
            Optional[PolicyOutput]: Selected action and arguments, or None.

        Example:
            >>> policy = ReactPolicy(llm=language_model)
            >>> output = await policy.async_select_action(belief)
            >>> if output:
            ...     print(output.action.name)
            'SearchCode'
        """
        return self.select_action(belief)

    def select_action(self, belief: Belief) -> Optional[PolicyOutput]:
        """Select an action based on current belief state.

        This method analyzes the current state and available actions using
        the ReAct framework to select the most appropriate next action.
        For trivial cases (single action with no args), it skips the
        language model reasoning.

        Args:
            belief (Belief): Current belief state of the agent.

        Returns:
            Optional[PolicyOutput]: Selected action and arguments, or None
                                  if selected action not found.

        Raises:
            SherpaPolicyException: If selected action not in available actions.

        Example:
            >>> policy = ReactPolicy(llm=language_model)
            >>> belief.actions = [SearchAction(), AnalyzeAction()]
            >>> output = policy.select_action(belief)
            >>> print(output.action.name)  # Based on reasoning
            'SearchAction'
        """
        actions = belief.get_actions()

        if is_selection_trivial(actions):
            return PolicyOutput(action=actions[0], args={})

        task_description = belief.current_task.content
        possible_actions = "\n".join([str(action) for action in actions])
        history_of_previous_actions = belief.get_internal_history(
            self.llm.get_num_tokens
        )

        response_format = json.dumps(self.response_format, indent=4)

        variables = {
            "role_description": self.role_description,
            "output_instruction": self.output_instruction,
            "task_description": task_description,
            "possible_actions": possible_actions,
            "history_of_previous_actions": history_of_previous_actions,
            "response_format": response_format,
        }
        prompt = self.prompt_template.format_prompt(
            prompt_parent_id="react_policy_prompt",
            prompt_id="SELECTION_DESCRIPTION",
            version="1.0",
            variables=variables,
        )
        logger.debug(f"Prompt: {prompt}")
        result = self.llm.invoke(prompt)
        # Handle both string and Message responses
        result_text = result.content if hasattr(result, 'content') else str(result)
        logger.debug(f"Result: {result_text}")

        name, args = transform_json_output(result_text)

        action = belief.get_action(name)

        if action is None:
            raise SherpaPolicyException(
                f"Action {name} not found in the list of possible actions"
            )

        return PolicyOutput(action=action, args=args)
