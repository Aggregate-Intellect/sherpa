from typing import Any

from loguru import logger

from sherpa_ai.actions.base import BaseAction, BaseRetrievalAction
from sherpa_ai.config.task_config import AgentConfig


class ChainActions(BaseAction):
    """A class for executing a sequence of actions in a chain.
    
    This class provides functionality to execute multiple actions in sequence,
    where each action's output can be used as input for subsequent actions.
    It manages the flow of data between actions and handles both single and
    multiple outputs from each action.
    
    This class inherits from :class:`BaseAction` and provides:
      - Sequential execution of multiple actions
      - Dynamic argument passing between actions
      - Support for both single and multiple outputs
      - Flexible action chaining configuration
    
    Attributes:
        actions (list[BaseAction]): List of actions to be executed in sequence.
        instruction (list[dict]): Configuration for how to pass data between actions.
    
    Example:
        >>> from sherpa_ai.actions import ChainActions, GoogleSearch, SynthesizeOutput
        >>> search = GoogleSearch(role_description="Researcher")
        >>> synthesize = SynthesizeOutput(role_description="Writer")
        >>> chain = ChainActions(
        ...     actions=[search, synthesize],
        ...     instruction=[
        ...         {},  # First action uses input kwargs
        ...         {"query": {"action": 0, "output": 0}}  # Second action uses first action's output
        ...     ]
        ... )
        >>> result = chain.execute(query="quantum computing")
    """
    actions: list[BaseAction]
    instruction: list[dict]

    def execute(self, **kwargs):
        """Execute the chain of actions.

        This method executes the sequence of actions in the order specified by the
        `instruction` list. It passes data between actions based on the provided
        instructions and handles both single and multiple outputs from each action.

        Args:
            **kwargs: Additional keyword arguments for the action.
            
        Returns:
            str: The processed search results as a string.

        Raises:
            SherpaActionExecutionException: If the action fails to execute.
        """
        output_list = [[""]]
        for i in range(len(self.actions)):
            kwargs_act = self.instruction[i]
            if i != 0 and len(kwargs_act) != 0:
                for key, value in kwargs_act.items():
                    if "output" not in value.keys():
                        kwargs_act[key] = output_list[value["action"]][0]
                    else:
                        kwargs_act[key] = output_list[value["action"]][value["output"]]
                res = self.actions[i](**kwargs_act)
            elif i != 0 and len(kwargs_act) == 0:
                res = self.actions[i]()
            elif i == 0:
                res = self.actions[i](**kwargs)
            if type(res) is tuple:
                output_list.append([it_res for it_res in res])
            else:
                output_list.append([res])
        return self.actions[-1](**kwargs_act)
