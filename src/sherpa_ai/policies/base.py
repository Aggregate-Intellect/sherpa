from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel

from sherpa_ai.actions.base import BaseAction


if TYPE_CHECKING:
    from sherpa_ai.memory.belief import Belief


class PolicyOutput(BaseModel):
    """
    The output of the policy

    Attributes:
        action (BaseAction): The action to be taken
        args (dict): The arguments for the selected action
    """

    action: Any  # TODO: Currently, we cannot use BaseAction since it does not inherit from Base class.
    args: dict


class BasePolicy(ABC, BaseModel):
    """
    The base class for a policy to select an action from the belief
    """

    @abstractmethod
    def select_action(self, belief: Belief, **kwargs) -> Optional[PolicyOutput]:
        pass

    def __call__(self, belief: Belief, **kwargs) -> Optional[PolicyOutput]:
        return self.select_action(belief, **kwargs)
