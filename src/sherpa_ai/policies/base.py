"""Base policy classes for Sherpa AI.

This module provides base classes for implementing agent policies.
It defines the core interfaces that all policies must implement,
including action selection and execution.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel

if TYPE_CHECKING:
    from sherpa_ai.memory.belief import Belief


class PolicyOutput(BaseModel):
    """Output from policy action selection.

    This class represents the result of a policy's action selection process,
    including both the selected action and its arguments.

    Attributes:
        action (Any): The action to be executed. Currently Any type due to
                     BaseAction not inheriting from BaseModel.
        args (dict): Arguments to pass to the selected action.

    Example:
        >>> output = PolicyOutput(
        ...     action=SearchAction(),
        ...     args={"query": "python programming"}
        ... )
        >>> print(output.args["query"])
        'python programming'
    """

    action: Any = (
        None
        # TODO: Currently, we cannot use BaseAction since it does not inherit
        # from Base class.
    )
    args: dict


class BasePolicy(ABC, BaseModel):
    """Abstract base class for agent policies.

    This class defines the interface that all policies must implement.
    Policies are responsible for selecting actions based on the agent's
    current belief state.

    Example:
        >>> class MyPolicy(BasePolicy):
        ...     def select_action(self, belief):
        ...         return PolicyOutput(action=SearchAction(), args={})
        >>> policy = MyPolicy()
        >>> output = policy(belief)
        >>> print(output.action)
        SearchAction()
    """

    @abstractmethod
    def select_action(self, belief: Belief, **kwargs) -> Optional[PolicyOutput]:
        """Select an action based on current belief state.

        Args:
            belief (Belief): Agent's current belief state.
            **kwargs: Additional arguments for action selection.

        Returns:
            Optional[PolicyOutput]: Selected action and arguments, or None
                                  if no action should be taken.

        Example:
            >>> policy = MyPolicy()
            >>> output = policy.select_action(belief)
            >>> if output:
            ...     print(output.action)
            SearchAction()
        """
        pass

    def __call__(self, belief: Belief, **kwargs) -> Optional[PolicyOutput]:
        """Convenience method for calling select_action.

        This method allows policies to be called directly as functions,
        delegating to select_action.

        Args:
            belief (Belief): Agent's current belief state.
            **kwargs: Additional arguments for action selection.

        Returns:
            Optional[PolicyOutput]: Selected action and arguments, or None
                                  if no action should be taken.

        Example:
            >>> policy = MyPolicy()
            >>> output = policy(belief)  # Same as policy.select_action(belief)
            >>> if output:
            ...     print(output.action)
            SearchAction()
        """
        return self.select_action(belief, **kwargs)
