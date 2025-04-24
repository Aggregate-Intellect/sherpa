from abc import ABC
from typing import Any

from pydantic import BaseModel, Field


class Event(BaseModel, ABC):
    """
    Base class for an event.
    """

    #: Name of the event.
    name: str

    def __str__(self) -> str:
        return repr(self)


class GenericEvent(Event):
    """
    Represents a generic event with default behavior.

    The `GenericEvent` class is a flexible event type that can store the event's name,
    content, and type. It can be used to handle a variety of event scenarios specific
    to the need of the application.

    Handled Event Types (Handled internally in Sherpa):
        - `task`: Indicates an event for registering a task for the agent.
        - `user_input`: Indicates an event for adding user inputs.

    Example:
        >>> event = GenericEvent(name="user_message", content="Hello, world!", event_type="user_input")
        >>> print(event.name)
        user_message
        >>> print(event.content)
        Hello, world!
        >>> print(event.event_type)
        user_input

    Notes:
        - The `event_type` attribute should be customized but defaults to "generic".
    """  # noqa: E501

    #: The name of the event.
    name: str
    #: The content or payload associated with the event.
    #: This can be any data relevant to the event.
    content: Any
    #: The type of the event. Defaults to "generic".
    event_type: str = "generic"


class ActionStartEvent(Event):
    """
    Represents an event triggered when an action is executed.

    This class is a specialized type of `Event` that captures the details of an action
    being started. It includes the name of the action, any arguments passed to the
    action, and a predefined event type (`action_start`).

    Example:
        >>> event = ActionStartEvent(name="fetch_data", args={"url": "https://example.com"})
        >>> print(event.name)
        fetch_data
        >>> print(event.args)
        {'url': 'https://example.com'}
        >>> print(event.event_type)
        action_start

    Notes:
        - The `event_type` attribute is fixed to "action_start" and cannot be changed.
    """  # noqa: E501

    #: The name of the action being executed.
    name: str
    #: A dictionary containing the arguments passed to the action.
    args: dict[str, Any]
    #: The type of the event, which is always set to "action_start".
    event_type: str = Field("action_start", frozen=True)


class ActionFinishEvent(Event):
    """
    Represents an event triggered when an action is completed.

    This class is a specialized type of `Event` that captures the details of an action
    that has finished execution. It includes the name of the action, the outputs or results
    of the action, and a predefined event type (`action_finish`).

    Example:
        >>> event = ActionFinishEvent(name="fetch_data", outputs={"status": "success", "data": [1, 2, 3]})
        >>> print(event.name)
        fetch_data
        >>> print(event.outputs)
        {'status': 'success', 'data': [1, 2, 3]}
        >>> print(event.event_type)
        action_finish

    Notes:
        - The `event_type` attribute is fixed to "action_finish" and should not be changed.
    """  # noqa: E501

    #: The name of the action that was executed.
    name: str
    #: The outputs or results produced by the action.
    outputs: Any
    #: The type of the event, which is always set to "action_finish".
    event_type: str = Field("action_finish", frozen=True)


def build_event(event_type: str, name: str, **kwargs) -> Event:
    """
    Build an event based on the event type.

    This is a factory function creating and returning the appropriate Event object based on
    the specified event_type. It handles creating specialized events like ActionStartEvent
    and ActionFinishEvent, falling back to GenericEvent for other event types.

    Args:
        event_type (str): The type of event to create. Special handling for "action_start"
            and "action_finish" (Mapped to their respective classes). All other values create
            a GenericEvent.
        name (str): The name of the event.
        **kwargs: Additional keyword arguments to pass to the event constructor.
            - For "action_start": Should include 'args' dictionary.
            - For "action_finish": Should include 'outputs' with results.
            - For other event types: Should include 'content' for the event payload.
    Returns:
        Event: An instance of the appropriate Event subclass:
            - ActionStartEvent for "action_start" event_type
            - ActionFinishEvent for "action_finish" event_type
            - GenericEvent for all other event_type values
    Example:
        >>> start_event = build_event("action_start", "fetch_data", args={"url": "example.com"})
        >>> finish_event = build_event("action_finish", "fetch_data", outputs={"status": "success"})
        >>> generic_event = build_event("user_input", "user_query", content="How are you?")
    """  # noqa: E501

    if event_type == "action_start":
        return ActionStartEvent(**kwargs, name=name)
    elif event_type == "action_finish":
        return ActionFinishEvent(**kwargs, name=name)
    else:
        return GenericEvent(**kwargs, event_type=event_type, name=name)
