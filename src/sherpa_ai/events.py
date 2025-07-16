from abc import ABC
from typing import Any

from pydantic import BaseModel, Field


class Event(BaseModel, ABC):
    """Base class for all events in the system.

    This abstract base class defines the common interface for all event types in the system.
    It inherits from both Pydantic's BaseModel for data validation and ABC for abstract base class functionality.

    Attributes:
        name (str): Name of the event, used for identification and logging.

    Example:
        >>> class CustomEvent(Event):
        ...     pass
        >>> event = CustomEvent(name="custom_event")
        >>> print(event.name)
        custom_event
    """  # noqa: E501

    #: Name of the event.
    name: str
    # Sender of the event, if applicable.
    sender: str = ""
    event_type: str

    def __str__(self) -> str:
        return repr(self)


class GenericEvent(Event):
    """A flexible event type that can handle various event scenarios.

    This class provides a generic event implementation that can store any type of content
    and event type. It's particularly useful for handling user inputs and task registrations.

    This class inherits from :class:`Event` and provides methods to:
        - Store and retrieve event content
        - Handle different event types
        - Provide string representation of events

    Attributes:
        name (str): The name of the event.
        content (Any): The content or payload associated with the event.
        event_type (str): The type of the event, defaults to "generic".

    Example:
        >>> from sherpa_ai.events import GenericEvent
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


class TriggerEvent(Event):
    """Event to trigger a state transition.

    This class represents an event that triggers a state transition in the system.
    It captures the event name and its associated arguments. This is useful for
    handling user inputs and message communications through the shared memory.

    Attributes:
        name (str): The name of the event being triggered.
        content (Any): A dictionary containing the arguments passed to the action.
        event_type (str): The type of the event, fixed to "trigger".

    Example:
        >>> from sherpa_ai.events import TriggerEvent
        >>> event = TriggerEvent(name="user_input", args={"message": "Hello, world!"})
        >>> print(event.name)
        user_input
    """  # noqa: E501

    #: The name of the event being triggered.
    name: str
    #: A dictionary containing the arguments passed to the action.
    args: dict[str, Any]
    #: The type of the event, which is always set to "action_start".
    event_type: str = Field("trigger", frozen=True)


class ActionStartEvent(Event):
    """Event triggered when an action begins execution.

    This class represents the start of an action execution, capturing the action name
    and its arguments. It's used for tracking and logging action execution flow.

    This class inherits from :class:`Event` and provides methods to:
        - Track action execution start
        - Store action arguments
        - Provide immutable event type

    Attributes:
        name (str): The name of the action being executed.
        args (dict[str, Any]): Dictionary containing the arguments passed to the action.
        event_type (str): The type of the event, fixed to "action_start".

    Example:
        >>> from sherpa_ai.events import ActionStartEvent
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
    """Event triggered when an action completes execution.

    This class represents the completion of an action execution, capturing the action name
    and its outputs. It's used for tracking and logging action execution results.

    This class inherits from :class:`Event` and provides methods to:
        - Track action execution completion
        - Store action outputs
        - Provide immutable event type

    Attributes:
        name (str): The name of the action that was executed.
        outputs (Any): The outputs or results produced by the action.
        event_type (str): The type of the event, fixed to "action_finish".

    Example:
        >>> from sherpa_ai.events import ActionFinishEvent
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
    """Factory function to create appropriate Event objects based on event type.

    This function creates and returns the appropriate Event subclass instance based on
    the specified event_type. It handles specialized events like ActionStartEvent and
    ActionFinishEvent, falling back to GenericEvent for other event types.

    Args:
        event_type (str): The type of event to create. Special handling for "action_start"
            and "action_finish". All other values create a GenericEvent.
        name (str): The name of the event.
        **kwargs: Additional keyword arguments to pass to the event constructor.
            For "action_start": Should include 'args' dictionary.
            For "action_finish": Should include 'outputs' with results.
            For other event types: Should include 'content' for the event payload.

    Returns:
        Event: An instance of the appropriate Event subclass:
            - ActionStartEvent for "action_start" event_type
            - ActionFinishEvent for "action_finish" event_type
            - GenericEvent for all other event_type values

    Example:
        >>> from sherpa_ai.events import build_event
        >>> start_event = build_event("action_start", "fetch_data", args={"url": "example.com"})
        >>> finish_event = build_event("action_finish", "fetch_data", outputs={"status": "success"})
        >>> generic_event = build_event("user_input", "user_query", content="How are you?")
    """  # noqa: E501

    if event_type == "action_start":
        return ActionStartEvent(**kwargs, name=name)
    elif event_type == "action_finish":
        return ActionFinishEvent(**kwargs, name=name)
    elif event_type == "trigger":
        if not kwargs.get("args"):
            # Default to no args if not provided
            kwargs["args"] = {}
        return TriggerEvent(name=name, **kwargs)
    else:
        return GenericEvent(**kwargs, event_type=event_type, name=name)
