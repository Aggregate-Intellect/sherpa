from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING, ClassVar, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts.chat import ChatPromptTemplate
from loguru import logger
from pydantic import BaseModel, ConfigDict

from sherpa_ai.actions.base import BaseAction
from sherpa_ai.policies.base import BasePolicy, PolicyOutput
from sherpa_ai.policies.exceptions import SherpaPolicyException
from sherpa_ai.policies.utils import (
    construct_conversation_from_belief,
    is_selection_trivial,
    transform_json_output,
)
from sherpa_ai.prompts.prompt_template_loader import PromptTemplate

if TYPE_CHECKING:
    from sherpa_ai.memory.belief import Belief


class ChatStateMachinePolicy(BasePolicy):
    """
    The policy to select an action from the belief based on the ReACT framework.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    # Initialize PromptTemplate as a class variable
    _prompt_template: ClassVar[PromptTemplate] = PromptTemplate(
        "./sherpa_ai/prompts/prompts.json"
    )

    # Initialize base templates with placeholder variables
    SYSTEM_PROMPT: ClassVar[str] = _prompt_template.format_prompt(
        prompt_parent_id="system_prompt",
        prompt_id="SYSTEM_PROMPT",
        version="1.0",
        variables={
            "context": "{context}",
            "task_description": "{task_description}",
            "response_format": "{response_format}",
        },
    )

    ACTION_SELECTION_PROMPT: ClassVar[str] = _prompt_template.format_prompt(
        prompt_parent_id="action_selection_prompt",
        prompt_id="ACTION_SELECTION_PROMPT",
        version="1.0",
        variables={
            "state": "{state}",
            "state_description": "{state_description}",
            "possible_actions": "{possible_actions}",
        },
    )

    # Initialize base chat template
    chat_template: ChatPromptTemplate = ChatPromptTemplate(
        [
            ("system", str(SYSTEM_PROMPT)),
            ("placeholder", "{conversation}"),
            ("human", str(ACTION_SELECTION_PROMPT)),
        ]
    )
    print("%" * 70)
    print(chat_template, flush=True)
    print("%" * 70)

    llm: Optional[BaseChatModel] = None
    response_format: dict = {
        "action": {
            "name": "action name you choose",
            "args": {"arg name": "value"},
        },
    }
    max_conversation_tokens: int = 8000

    def get_prompt_data(self, belief: Belief, actions: list[BaseAction]) -> dict:
        """Create the prompt based on information from the belief"""
        task_description = belief.current_task.content
        possible_actions = "\n".join([str(action) for action in actions])
        current_state = belief.get_state_obj().name
        state_description = belief.get_state_obj().description
        conversations = construct_conversation_from_belief(
            belief, self.llm.get_num_tokens, self.max_conversation_tokens
        )

        formatted_state_description = ""
        if state_description:
            variables = {"state": current_state, "state_description": state_description}
            formatted_state_description = self._prompt_template.format_prompt(
                prompt_parent_id="state_description_prompt",
                prompt_id="STATE_DESCRIPTION_PROMPT",
                version="1.0",
                variables=variables,
            )

        return {
            "task_description": task_description,
            "possible_actions": possible_actions,
            "state": current_state,
            "state_description": formatted_state_description,
            "response_format": json.dumps(self.response_format, indent=4),
            "conversation": conversations,
        }

    def select_action(self, belief: Belief) -> Optional[PolicyOutput]:
        """Synchronous wrapper for async_select_action"""
        return asyncio.run(self.async_select_action(belief))

    async def async_select_action(self, belief: Belief) -> Optional[PolicyOutput]:
        """Select an action based on the current belief state"""
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
