from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Optional

from loguru import logger

from sherpa_ai.policies.base import BasePolicy, PolicyOutput
from sherpa_ai.policies.exceptions import SherpaPolicyException
from sherpa_ai.policies.utils import (is_selection_trivial,
                                      transform_json_output)

if TYPE_CHECKING:
    from sherpa_ai.memory.belief import Belief

SELECTION_DESCRIPTION = """{role_description}

{output_instruction}

**Task Description**: {task_description}

**Possible Actions**:
{possible_actions}

**Task Context**:
{task_context}

**History of Previous Actions**:
{history_of_previous_actions}

You should only select the actions specified in **Possible Actions**
You should only respond in JSON format as described below without any extra text.
Response Format:
{response_format}
Ensure the response can be parsed by Python json.loads

Follow the described format strictly.

"""  # noqa: E501


class ReactPolicy(BasePolicy):
    """
    The policy to select an action from the belief based on the ReACT framework.

    See this paper for more details: https://arxiv.org/abs/2210.03629

    Attributes:
        role_description (str): The description of the agent role to help select an action
        output_instruction (str): The instruction to output the action in JSON format
        llm (BaseLanguageModel): The large language model used to generate text
        description (str): Description to select the action from the belief
        response_format (dict): The response format for the policy in JSON format
    """  # noqa: E501

    role_description: str
    output_instruction: str
    # Cannot use langchain's BaseLanguageModel due to they are using Pydantic v1
    llm: Any = None
    description: str = SELECTION_DESCRIPTION
    response_format: dict = {
        "command": {
            "name": "tool/command name you choose",
            "args": {"arg name": "value"},
        },
    }

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

        task_description = belief.current_task.content
        task_context = belief.get_context(self.llm.get_num_tokens)
        possible_actions = "\n".join([str(action) for action in actions])
        history_of_previous_actions = belief.get_internal_history(
            self.llm.get_num_tokens
        )

        response_format = json.dumps(self.response_format, indent=4)

        prompt = self.description.format(
            role_description=self.role_description,
            task_description=task_description,
            possible_actions=possible_actions,
            history_of_previous_actions=history_of_previous_actions,
            task_context=task_context,
            output_instruction=self.output_instruction,
            response_format=response_format,
        )
        logger.debug(f"Prompt: {prompt}")
        result = self.llm.predict(prompt)
        logger.debug(f"Result: {result}")

        name, args = transform_json_output(result)

        action = belief.get_action(name)

        if action is None:
            raise SherpaPolicyException(
                f"Action {name} not found in the list of possible actions"
            )

        return PolicyOutput(action=action, args=args)
