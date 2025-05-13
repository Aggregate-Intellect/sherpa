"""
A dynamic action that the behavior can be defined at runtime when creating the action.
"""

from typing import Callable

from sherpa_ai.actions.base import AsyncBaseAction, BaseAction


class DynamicAction(BaseAction):
    """A class for creating actions with runtime-defined behavior.
    
    This class provides functionality to create actions whose behavior is defined
    at runtime through a callable function. This allows for flexible and dynamic
    action creation without needing to define new classes.
    
    This class inherits from :class:`BaseAction` and provides:
      - Runtime behavior definition through callables
      - Dynamic execution of user-defined functions
      - Flexible argument handling
    
    Attributes:
        action (Callable): Function that defines the behavior of the action.
        name (str): Name of the action.
        args (dict): Arguments required by the action.
        usage (str): Description of the action's usage.
    
    Example:
        >>> from sherpa_ai.actions import DynamicAction
        >>> def my_action(x: int, y: int) -> int:
        ...     return x + y
        >>> action = DynamicAction(action=my_action)
        >>> result = action.execute(x=5, y=3)
        >>> print(result)
        8
    """

    action: Callable

    def execute(self, **kwargs):
        return self.action(**kwargs)


class AsyncDynamicAction(AsyncBaseAction):
    """A class for creating asynchronous actions with runtime-defined behavior.
    
    This class provides functionality to create asynchronous actions whose behavior
    is defined at runtime through an async callable function. This allows for flexible
    and dynamic async action creation without needing to define new classes.
    
    This class inherits from :class:`AsyncBaseAction` and provides:
      - Runtime behavior definition through async callables
      - Dynamic execution of user-defined async functions
      - Flexible argument handling for async operations
    
    Attributes:
        action (Callable): Async function that defines the behavior of the action.
        name (str): Name of the action.
        args (dict): Arguments required by the action.
        usage (str): Description of the action's usage.
    
    Example:
        >>> from sherpa_ai.actions import AsyncDynamicAction
        >>> async def my_async_action(x: int, y: int) -> int:
        ...     await asyncio.sleep(1)
        ...     return x + y
        >>> action = AsyncDynamicAction(action=my_async_action)
        >>> result = await action.execute(x=5, y=3)
        >>> print(result)
        8
    """

    action: Callable

    async def execute(self, **kwargs):
        return await self.action(**kwargs)
