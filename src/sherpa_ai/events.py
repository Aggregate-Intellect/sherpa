from abc import ABC
from typing import Any

from pydantic import BaseModel


class Event(BaseModel, ABC):
    """
    Base class for an event.
    """

    name: str

    def __str__(self) -> str:
        return repr(self)


class GenericEvent(Event):
    """
    Base class for an event.
    """

    name: str
    content: Any
    event_type: str = "generic"


class ActionStartEvent(Event):
    """
    Event triggered when an action is executed.
    """

    name: str
    args: dict[str, Any]
    event_type: str = "action_start"


class ActionFinishEvent(Event):
    """
    Event triggered when an action is executed.
    """

    name: str
    outputs: Any
    event_type: str = "action_finish"


def build_event(event_type: str, name: str, **kwargs) -> Event:
    """
    Build an event based on the event type.
    """
    if event_type == "action_start":
        return ActionStartEvent(**kwargs, event_type=event_type, name=name)
    elif event_type == "action_finish":
        return ActionFinishEvent(**kwargs, event_type=event_type, name=name)
    else:
        return GenericEvent(**kwargs, event_type=event_type, name=name)
