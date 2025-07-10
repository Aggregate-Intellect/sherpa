"""ReAct State Machine policy implementation for Sherpa AI.

This module provides a policy implementation that combines the ReAct framework
with state machine information for action selection. It defines the
ReactStateMachinePolicy class which uses both the current state and state
machine transitions to guide action selection.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Optional

from loguru import logger
from pydantic import BaseModel, ConfigDict
from langchain_core.language_models.base import BaseLanguageModel

from sherpa_ai.actions.base import BaseAction
from sherpa_ai.policies.base import BasePolicy, PolicyOutput
from sherpa_ai.policies.exceptions import SherpaPolicyException
from sherpa_ai.policies.utils import is_selection_trivial, transform_json_output
from sherpa_ai.prompts.prompt_template_loader import PromptTemplate

if TYPE_CHECKING:
    from sherpa_ai.memory.belief import Belief


class ReactStateMachinePolicy(BasePolicy):
    """Policy implementation combining ReAct framework with state machine.

    This class extends the ReAct framework by incorporating state machine
    information into the action selection process. It considers both the
    current state and possible state transitions when choosing actions.

    Attributes:
        role_description (str): Description of agent role for action selection.
        output_instruction (str): Instruction for JSON output format.
        llm (Any): Language model for generating text (BaseLanguageModel).
        prompt_template (PromptTemplate): Template for generating prompts.
        response_format (dict): Expected JSON format for responses.
        model_config (ConfigDict): Configuration allowing arbitrary types.

    Example:
        >>> policy = ReactStateMachinePolicy(
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

    def get_prompt(self, belief: Belief, actions: list[BaseAction]) -> str:
        """Create a prompt for action selection using belief and state info.

        This method generates a prompt that includes the current task,
        available actions, action history, current state, and state
        description to help guide action selection.

        Args:
            belief (Belief): Current belief state of the agent.
            actions (list[BaseAction]): List of available actions.

        Returns:
            str: Formatted prompt for the language model.

        Example:
            >>> prompt = policy.get_prompt(belief, actions)
            >>> print(prompt)  # Shows formatted prompt with state info
            'You are an assistant that helps with coding...'
        """
        task_description = belief.current_task.content
        possible_actions = "\n".join([str(action) for action in actions])
        history_of_previous_actions = belief.get_internal_history(
            self.llm.get_num_tokens
        )
        current_state = belief.get_state_obj().name
        state_description = belief.get_state_obj().description

        variables = {"state": current_state, "state_description": state_description}

        if len(state_description) > 0:
            state_description = self.prompt_template.format_prompt(
                prompt_parent_id="react_sm_policy_prompt",
                prompt_id="STATE_DESCRIPTION_PROMPT",
                version="1.0",
                variables=variables,
            )

        response_format = json.dumps(self.response_format, indent=4)

        prompt = self.prompt_template.format_prompt(
            prompt_parent_id="react_sm_policy_prompt",
            prompt_id="SELECTION_DESCRIPTION",
            version="1.0",
            variables={
                "role_description": self.role_description,
                "history_of_previous_actions": history_of_previous_actions,
                "state": current_state,
                "state_description": state_description,
                "possible_actions": possible_actions,
                "task_description": task_description,
                "response_format": response_format,
                "output_instruction": self.output_instruction,
            },
        )

        return prompt

    def select_action(self, belief: Belief) -> Optional[PolicyOutput]:
        """Select an action based on current belief state and state machine.

        This method analyzes the current state, available actions, and state
        machine information to select the most appropriate next action.
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
            >>> policy = ReactStateMachinePolicy(llm=language_model)
            >>> belief.actions = [SearchAction(), AnalyzeAction()]
            >>> output = policy.select_action(belief)
            >>> print(output.action.name)  # Based on state and reasoning
            'SearchAction'
        """
        actions = belief.get_actions()
        if is_selection_trivial(actions):
            return PolicyOutput(action=actions[0], args={})

        prompt = self.get_prompt(belief, actions)
        logger.debug(f"Prompt: {prompt}")
        result = self.llm.invoke(prompt)
        result_text = result.content if hasattr(result, "content") else str(result)
        logger.debug(f"Result: {result_text}")

        name, args = transform_json_output(result_text)

        action = belief.get_action(name)

        if action is None:
            raise SherpaPolicyException(
                f"Action {name} not found in the list of possible actions"
            )

        return PolicyOutput(action=action, args=args)

    async def async_select_action(self, belief: Belief) -> Optional[PolicyOutput]:
        """Asynchronously select an action based on belief state and state machine.

        This method provides an asynchronous version of action selection,
        considering the current state, available actions, and state machine
        information.

        Args:
            belief (Belief): Current belief state of the agent.

        Returns:
            Optional[PolicyOutput]: Selected action and arguments, or None
                                  if selected action not found.

        Raises:
            SherpaPolicyException: If selected action not in available actions.

        Example:
            >>> policy = ReactStateMachinePolicy(llm=language_model)
            >>> output = await policy.async_select_action(belief)
            >>> if output:
            ...     print(output.action.name)
            'SearchAction'
        """
        actions = await belief.async_get_actions()
        if is_selection_trivial(actions):
            return PolicyOutput(action=actions[0], args={})

        prompt = self.get_prompt(belief, actions)
        logger.debug(f"Prompt: {prompt}")
        result = await self.llm.ainvoke(prompt)
        result_text = result.content if hasattr(result, "content") else str(result)
        logger.debug(f"Result: {result_text}")

        name, args = transform_json_output(result_text)

        action = await belief.async_get_action(name)

        if action is None:
            raise SherpaPolicyException(
                f"Action {name} not found in the list of possible actions"
            )

        return PolicyOutput(action=action, args=args)
