from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts.chat import ChatPromptTemplate
from loguru import logger

from sherpa_ai.actions.base import BaseAction
from sherpa_ai.policies.base import BasePolicy, PolicyOutput
from sherpa_ai.policies.exceptions import SherpaPolicyException
from sherpa_ai.policies.utils import (construct_conversation_from_belief,
                                      is_selection_trivial,
                                      transform_json_output)

if TYPE_CHECKING:
    from sherpa_ai.memory.belief import Belief

SYSTEM_PROMPT = """You are an assistant that must parse the user’s instructions and select the most appropriate action from the provided possibilities. Only respond with valid JSON as described, without any extra text. Comply strictly with the specified format.

## Context
{context}

**Task Description**: {task_description}

You should only respond in JSON format as described below without any extra text.
Response Format:
{response_format}
Ensure the response can be parsed by Python json.loads
"""  # noqa: E501

ACTION_SELECTION_PROMPT = """You have a state machine to help you with the action execution. You are currently in the {state} state.
{state_description}

## Possible Actions:
{possible_actions}

You should only select the actions specified in **Possible Actions**
First, reason about what to do next based on the information, then select the best action.
"""  # noqa: E501

STATE_DESCRIPTION_PROMPT = """The {state} state has the following instruction:
{state_description}
"""


class ReactStateMachinePolicy(BasePolicy):
    """
    The policy to select an action from the belief based on the ReACT framework.

    If uses information from the state machine

    Attributes:
        chat_template: The template used to generate the chat prompt, it should have
            the following placeholder variable: {conversation} It should at least have
            the following valued variables to support state machine information:
            {state}, {state_description}, {possible_actions}
        llm (BaseChatLanguageModel): The large language model used to generate text
        response_format (dict): The response format for the policy in JSON format,
        ignored if chat_template is provided
        max_conversation_tokens (int): The maximum number of tokens to generate for the
            conversation, defaults to 8000
    """

    chat_template: ChatPromptTemplate = ChatPromptTemplate(
        [
            ("system", SYSTEM_PROMPT),
            ("placeholder", "{conversation}"),
            ("human", ACTION_SELECTION_PROMPT),
        ]
    )
    # Cannot use langchain's BaseLanguageModel due to they are using Pydantic v1
    llm: BaseChatModel = None

    response_format: dict = {
        "action": {
            "name": "action name you choose",
            "args": {"arg name": "value"},
        },
    }
    max_conversation_tokens: int = 8000

    def get_prompt_data(self, belief: Belief, actions: list[BaseAction]) -> dict:
        """
        Create the prompt based on information from the belief

        Args:
            belief (Belief): The current state of the agent

        Returns:
            dict: The prompt data to be used for the selection of the action
        """
        task_description = belief.current_task.content
        possible_actions = "\n".join([str(action) for action in actions])
        context = belief.get_context(self.llm.get_num_tokens)
        current_state = belief.get_state_obj().name
        state_description = belief.get_state_obj().description
        conversations = construct_conversation_from_belief(
            belief, self.llm.get_num_tokens, self.max_conversation_tokens
        )

        if len(state_description) > 0:
            state_description = STATE_DESCRIPTION_PROMPT.format(
                state=current_state, state_description=state_description
            )

        response_format = json.dumps(self.response_format, indent=4)

        return {
            "context": context,
            "task_description": task_description,
            "possible_actions": possible_actions,
            "state": current_state,
            "state_description": state_description,
            "response_format": response_format,
            "conversation": conversations,
        }

    def select_action(self, belief: Belief) -> Optional[PolicyOutput]:
        """
        Select an action from a list of possible actions based on the current state (belief)
        Calling the async version of the method with asyncio

        Args:
            belief (Belief): The current state of the agent

        Returns:
            Optional[PolicyOutput]: The selected action and arguments, or None if the selected
            action is not found in the list of possible actions
        """  # noqa: E501
        result = asyncio.run(self.async_select_action(belief))

        return result

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

        prompt_data = self.get_prompt_data(belief, actions)
        logger.debug(f"Prompt: {self.chat_template.invoke(prompt_data)}")
        chain = self.chat_template | self.llm
        result = chain.invoke(prompt_data).content
        logger.debug(f"Result: {result}")

        name, args = transform_json_output(result)

        action = await belief.async_get_action(name)

        if action is None:
            raise SherpaPolicyException(
                f"Action {name} not found in the list of possible actions"
            )

        return PolicyOutput(action=action, args=args)
