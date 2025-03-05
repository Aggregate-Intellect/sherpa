from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Optional

from loguru import logger
from pydantic import BaseModel, ConfigDict
from sherpa_ai.actions.base import BaseAction
from sherpa_ai.policies.base import BasePolicy, PolicyOutput
from sherpa_ai.policies.exceptions import SherpaPolicyException
from sherpa_ai.prompts.prompt_template_loader import PromptTemplate
from sherpa_ai.policies.utils import (is_selection_trivial,
                                      transform_json_output)

if TYPE_CHECKING:
    from sherpa_ai.memory.belief import Belief


class ReactStateMachinePolicy(BasePolicy):
    """
    The policy to select an action from the belief based on the ReACT framework.

    If uses information from the state machine

    Attributes:
        role_description (str): The description of the agent role to help select an action
        output_instruction (str): The instruction to output the action in JSON format
        llm (BaseLanguageModel): The large language model used to generate text
        response_format (dict): The response format for the policy in JSON format
    """  # noqa: E501
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )
    role_description: str
    output_instruction: str
    # Cannot use langchain's BaseLanguageModel due to they are using Pydantic v1
    llm: Any = None
    prompt_template: PromptTemplate = PromptTemplate("./sherpa_ai/prompts/prompts.json")

    response_format: dict = {
        "command": {
            "name": "tool/command name you choose",
            "args": {"arg name": "value"},
        },
    }

    def get_prompt(self, belief: Belief, actions: list[BaseAction]) -> str:
        """
        Create the prompt based on information from the belief

        Args:
            belief (Belief): The current state of the agent

        Returns:
            str: The prompt to be used for the selection of the action
        """
        task_description = belief.current_task.content
        possible_actions = "\n".join([str(action) for action in actions])
        context = belief.get_context(self.llm.get_num_tokens)
        history_of_previous_actions = belief.get_internal_history(
            self.llm.get_num_tokens
        )
        current_state = belief.get_state_obj().name
        state_description = belief.get_state_obj().description

        variables ={
            "state": current_state,
            "state_description": state_description
        }

        if len(state_description) > 0:
            state_description = self.prompt_template.format_prompt(
                wrapper= "react_sm_policy_prompt",
                name="STATE_DESCRIPTION_PROMPT",
                version="1.0",
                variables=variables
            )

        response_format = json.dumps(self.response_format, indent=4)

        prompt = self.prompt_template.format_prompt(
            wrapper="react_sm_policy_prompt",
            name = "SELECTION_DESCRIPTION",
            version="1.0",
            variables={
                "role_description":self.role_description,
                "context":context,
                "history_of_previous_actions":history_of_previous_actions,
                "state":current_state,
                "state_description":state_description,
                "possible_actions":possible_actions,
                "task_description":task_description,
                "response_format":response_format,
                "output_instruction":self.output_instruction
            }
        )

        return prompt

    def select_action(self, belief: Belief) -> Optional[PolicyOutput]:
        """
        Select an action from a list of possible actions based on the current state (belief)

        Args:
            belief (Belief): The current state of the agent

        Returns:
            Optional[PolicyOutput]: The selected action and arguments, or None if the selected
            action is not found in the list of possible actions
        """  # noqa: E501
        actions = belief.get_actions()
        if is_selection_trivial(actions):
            return PolicyOutput(action=actions[0], args={})

        prompt = self.get_prompt(belief, actions)
        logger.debug(f"Prompt: {prompt}")
        result = self.llm.invoke(prompt)
        result_text = result.content if hasattr(result, 'content') else str(result)
        logger.debug(f"Result: {result_text}")

        name, args = transform_json_output(result_text)

        action = belief.get_action(name)

        if action is None:
            raise SherpaPolicyException(
                f"Action {name} not found in the list of possible actions"
            )

        return PolicyOutput(action=action, args=args)

    async def async_select_action(self, belief: Belief) -> Optional[PolicyOutput]:
        """
        Select an action from a list of possible actions based on the current state (belief)

        Args:
            belief (Belief): The current state of the agent

        Returns:
            Optional[PolicyOutput]: The selected action and arguments, or None if the selected
            action is not found in the list of possible actions
        """  # noqa: E501
        actions = await belief.async_get_actions()
        if is_selection_trivial(actions):
            return PolicyOutput(action=actions[0], args={})

        prompt = self.get_prompt(belief, actions)
        logger.debug(f"Prompt: {prompt}")
        result = await self.llm.ainvoke(prompt)
        result_text = result.content if hasattr(result, 'content') else str(result)
        logger.debug(f"Result: {result_text}")

        name, args = transform_json_output(result_text)

        action = await belief.async_get_action(name)

        if action is None:
            raise SherpaPolicyException(
                f"Action {name} not found in the list of possible actions"
            )

        return PolicyOutput(action=action, args=args)
