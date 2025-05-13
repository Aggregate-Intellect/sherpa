from typing import Any, Optional, Union

from pydantic import PrivateAttr

from sherpa_ai.actions.base import BaseAction, ActionArgument


class MockAction(BaseAction):
    """A mock implementation of BaseAction for testing purposes.
    
    This class provides a simple implementation of BaseAction that returns a
    predefined value when executed, allowing for testing of agents and workflows
    without making real API calls or requiring external dependencies.
    
    This class inherits from :class:`BaseAction` and provides methods to:
      - Initialize a mock action with customizable parameters
      - Execute the action and return a predefined result
    
    Attributes:
        name (str): Name of the action.
        args (Union[dict, list[ActionArgument]]): Arguments required to run the action.
        usage (str): Usage description of the action.
        belief (Any): Belief used for the action. Optional.
        output_key (Optional[str]): Output key for storing the result. 
            Defaults to the action name.
        _return_value (str): The value returned when the action is executed.
    
    Example:
        >>> mock = MockAction(name="test_action", return_value="success")
        >>> result = mock.execute()
        >>> print(result)
        success
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
        """Initialize a MockAction with the provided parameters.
        
        Args:
            name (str): Name of the action.
            usage (str, optional): Usage description of the action. Defaults to "Mock usage".
            args (Union[dict, list[ActionArgument]], optional): Arguments required by the action. Defaults to {}.
            belief (Any, optional): Belief system for the action. Defaults to None.
            output_key (Optional[str], optional): Key for storing the result. Defaults to None.
            return_value (str, optional): Value to return when executed. Defaults to "Mock result".
        """
        super().__init__(
            name=name,
            usage=usage,
            args=args,
            belief=belief,
            output_key=output_key,
        )
        self._return_value = return_value

    def execute(self, **kwargs) -> str:
        """Execute the mock action and return a predefined result.
        
        This method simply returns the predefined return value, ignoring any
        input arguments.
        
        Args:
            **kwargs: Keyword arguments (ignored).
            
        Returns:
            str: The predefined mock result.
        """
        return self._return_value 