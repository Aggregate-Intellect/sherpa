from typing import Optional, Tuple

from langchain.base_language import BaseLanguageModel
from loguru import logger

from sherpa_ai.action_planner.base import BaseActionPlanner
from sherpa_ai.memory.belief import Belief

SELECTION_DESCRIPTION = """{role_description}

**Task Description**: {task_description}

**Possible Actions**:
{possible_actions}

**Task Context**:
{task_context}

**History of Previous Actions**:
{history_of_previous_actions}

Please respond in the following format strictly, do not Reformat the text:
"Action Name : ArgumentName1(Input Value); ArgumentName2(Input Value); ..."

If you believe the task is complete and no further actions are necessary, respond with "Finished".

{output_instruction}

Follow the described fromat strictly. Select only one action and use one argument exactly once.

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

    def transform_output(self, output_str: str) -> Tuple[str, dict]:
        """
        Transform the output string into an action and arguments

        Args:
            output_str: Output string

        Returns:
            str: Action to be taken
            dict: Arguments for the action
        """

        # Splitting the action name from the arguments
        action, args_str = output_str.split(":")

        # Extracting individual arguments
        args_list = args_str.split(";")

        logger.debug(f"Args: {args_list}")
        # Parsing arguments into a dictionary
        args_dict = {}
        for arg in args_list:
            if arg == "":
                continue
            arg_name, arg_value = arg.split("(")
            arg_value = arg_value.rstrip(")")

            args_dict[arg_name.strip()] = arg_value.strip()

        return (action.strip(), args_dict)

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

        prompt = self.description.format(
            role_description=self.role_description,
            task_description=task_description,
            possible_actions=possible_actions,
            history_of_previous_actions=history_of_previous_actions,
            task_context=task_context,
            output_instruction=self.output_instruction,
        )

        logger.debug(f"Prompt: {prompt}")
        result = self.llm.predict(prompt)
        result = result.split("\n")[0].strip()

        logger.debug(f"Result: {result}")

        if result == "Finished":
            return None

        return self.transform_output(result)
