from typing import Any, Optional, Union

from pydantic import PrivateAttr

from sherpa_ai.actions.base import BaseAction, ActionArgument


class MockAction(BaseAction):
    """
    A mock implementation of BaseAction for testing purposes.

    This class allows testing agents and workflows without making real API calls
    or requiring external dependencies.

    Attributes:
        name (str): Name of the action.
        args (Union[dict, list[ActionArgument]]): Arguments required to run the action.
        usage (str): Usage description of the action.
        belief (Any): Belief used for the action. Optional.
        output_key (Optional[str]): Output key for storing the result. 
            Defaults to the action name.
        return_value (str): The value returned when the action is executed.
    """

    _return_value: str = PrivateAttr()

    def __init__(
        self,
        name: str,
        usage: str = "Mock usage",
        args: Union[dict, list[ActionArgument]] = {},
        belief: Any = None,
        output_key: Optional[str] = None,
        return_value: str = "Mock result",
    ):
        super().__init__(
            name=name,
            usage=usage,
            args=args,
            belief=belief,
            output_key=output_key,
        )
        self._return_value = return_value

    def execute(self, **kwargs):
        """
        Execute the mock action and return a predefined result.

        Returns:
            str: The predefined mock result.
        """
        return self._return_value 