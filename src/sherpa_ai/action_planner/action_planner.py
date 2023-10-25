from __future__ import annotations

import json
from typing import TYPE_CHECKING, Optional, Tuple

from langchain.base_language import BaseLanguageModel
from loguru import logger

from sherpa_ai.action_planner.base import BaseActionPlanner

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

You should only respond in JSON format as described below without any extra text.
Response Format:
{response_format}
Ensure the response can be parsed by Python json.loads

If you believe the task is complete and no further actions are necessary, respond with "Finished".

Follow the described fromat strictly.

"""  # noqa: E501


class ActionPlanner(BaseActionPlanner):
    def __init__(
        self,
        role_description: str,
        output_instruction: str,
        llm: BaseLanguageModel,
        description: str = SELECTION_DESCRIPTION,
    ):
        self.description = description
        self.role_description = role_description
        self.output_instruction = output_instruction
        self.llm = llm

        self.response_format = {
            "command": {
                "name": "tool/command name you choose",
                "args": {"arg name": "value"},
            },
        }

    def transform_output(self, output_str: str) -> Tuple[str, dict]:
        """
        Transform the output string into an action and arguments

        Args:
            output_str: Output string

        Returns:
            str: Action to be taken
            dict: Arguments for the action
        """
        output = json.loads(output_str)
        command = output["command"]
        name = command["name"]
        args = command.get("args", {})
        return name, args

    def select_action(
        self,
        belief: Belief,
    ) -> Optional[Tuple[str, dict]]:
        """
        Select an action from a list of possible actions

        Args:
            task_description: Description of the task
            task_context: Context of the task (e.g. events from previous agents)
            possible_actions: List of possible actions
            history_of_previous_actions: History of previous actions

        Returns:
            str: Action to be taken
            dict: Arguments for the action
        """
        task_description = belief.current_task.content
        task_context = belief.get_context(self.llm.get_num_tokens)
        possible_actions = belief.action_description
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

        if result == "Finished":
            return None

        name, args = self.transform_output(result)

        if name == "Finished":
            return None
        
        return name, args