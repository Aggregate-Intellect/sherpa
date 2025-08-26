"""Belief management module for Sherpa AI.

This module provides belief tracking functionality for agents in the Sherpa AI system.
It defines the Belief class which manages agent state, events, and internal reasoning.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Dict, List, Optional

import pydash
import transitions as ts
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field

from sherpa_ai.events import Event, build_event
from sherpa_ai.memory.state_machine import SherpaStateMachine

if TYPE_CHECKING:
    from sherpa_ai.actions.base import BaseAction


class Belief(BaseModel):
    """Manages agent beliefs and state tracking.

    This class maintains the agent's belief state, including observed events,
    internal reasoning events, and current task information. It provides methods
    for updating and retrieving belief state, managing events, and handling
    agent actions.

    Attributes:
        events (List[Event]): List of events observed by the agent.
        internal_events (List[Event]): List of internal events from agent reasoning.
        current_task (Event): The current task being processed.
        state_machine (SherpaStateMachine): State machine for managing agent state.
        actions (List[BaseAction]): List of available actions.
        belief_data (dict): Dictionary for storing arbitrary belief data.
        max_tokens (int): Maximum number of tokens for context/history.

    Example:
        >>> belief = Belief()
        >>> belief.update(observation_event)
        >>> belief.set_current_task("Analyze the data")
        >>> context = belief.get_context(token_counter)
        >>> print(context)
        'current_task: Analyze the data(task)'
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
    events: List[Event] = Field(default_factory=list)
    internal_events: List[Event] = Field(default_factory=list)
    current_task: Event = None
    state_machine: SherpaStateMachine = None
    actions: List = Field(default_factory=list)
    belief_data: Dict = Field(default_factory=dict)
    max_tokens: int = 4000

    def update(self, observation: Event):
        """Update belief with a new observation event.

        Args:
            observation (Event): The event to add to the belief state.

        Example:
            >>> belief = Belief()
            >>> event = Event("observation", "user_input", "Hello")
            >>> belief.update(event)
            >>> print(belief.events)
            [Event("observation", "user_input", "Hello")]
        """
        if observation in self.events:
            return

        self.events.append(observation)

    def get_context(self, token_counter: Callable[[str], int]):
        """Get the context of the agent's belief state.

        Args:
            token_counter (Callable[[str], int]): Function to count tokens in text.

        Returns:
            str: Context string containing relevant events, truncated if exceeding max_tokens.

        Example:
            >>> belief = Belief()
            >>> def count_tokens(text): return len(text.split())
            >>> belief.set_current_task("Analyze data")
            >>> context = belief.get_context(count_tokens)
            >>> print(context)
            'current_task: Analyze data(task)'
        """  # noqa: E501
        context = ""
        for event in reversed(self.events):
            if event.event_type in [
                "task",
                "result",
                "user_input",
            ]:
                message = f"{event.name}: {event.content}({event.event_type})"
                context = message + "\n" + context

                if token_counter(context) > self.max_tokens:
                    break

        return context

    def update_internal(self, event_type: str, name: str, **kwargs):
        """Add an internal event to the belief state.

        Args:
            event_type (str): Type of the internal event.
            name (str): Name of the event.
            **kwargs: Additional event parameters.

        Example:
            >>> belief = Belief()
            >>> belief.update_internal("reasoning", "analysis", content="Processing data")
            >>> print(belief.internal_events[0].event_type)
            'reasoning'
        """  # noqa: E501
        event = build_event(event_type, name, **kwargs)
        self.internal_events.append(event)

    def get_by_type(self, event_type):
        """Get all internal events of a specific type.

        Args:
            event_type (str): Type of events to retrieve.

        Returns:
            List[Event]: List of internal events matching the type.

        Example:
            >>> belief = Belief()
            >>> belief.update_internal("reasoning", "analysis")
            >>> events = belief.get_by_type("reasoning")
            >>> print(len(events))
            1
        """
        return [
            event for event in self.internal_events if event.event_type == event_type
        ]

    def get_events_by_type(self, event_type: str) -> List[dict]:
        """Retrieve events of a specific type as JSON objects.

        Args:
            event_type (str): The type of events to retrieve (e.g., "action_start", "feedback").

        Returns:
            List[dict]: A list of events as JSON objects, in chronological order (oldest to newest).
                Each object contains the event's properties (name, content, event_type, etc.).

        Example:
            >>> belief = Belief()
            >>> belief.update_internal("action_start", "test_action", args={"param": "value"})
            >>> events = belief.get_events_by_type("action_start")
            >>> print(events[0]["name"])
            test_action
        """
        return [event.model_dump() for event in self.internal_events if event.event_type == event_type]

    def get_events_excluding_types(self, exclude_types: List[str]) -> List[dict]:
        """Retrieve events excluding specific types as JSON objects.

        Args:
            exclude_types (List[str]): List of event types to exclude from the results (e.g., ["feedback", "action_start"]).

        Returns:
            List[dict]: A list of events as JSON objects, in chronological order (oldest to newest),
                excluding events whose types are in the exclude_types list.

        Example:
            >>> belief = Belief()
            >>> belief.update_internal("action_start", "action1", args={})
            >>> belief.update_internal("feedback", "feedback1", content="good")
            >>> events = belief.get_events_excluding_types(["feedback"])
            >>> print(events[0]["event_type"])
            action_start
        """
        return [event.model_dump() for event in self.internal_events if event.event_type not in exclude_types]

    def set_current_task(self, content):
        """Set the current task in the belief state.

        Args:
            content (str): Content of the current task.

        Example:
            >>> belief = Belief()
            >>> belief.set_current_task("Process data")
            >>> print(belief.current_task.content)
            'Process data'
        """
        event = build_event("task", "current_task", content=content)
        self.current_task = event

    def get_internal_history(self, token_counter: Callable[[str], int]):
        """Get the internal history of the agent as a string, with token limiting.

        This method uses get_events_excluding_types to retrieve all internal events as dicts,
        then converts them to strings in reverse order (most recent first) for LLM context,
        and applies token limiting.

        Args:
            token_counter (Callable[[str], int]): Function to count tokens in text.

        Returns:
            str: Internal history string, in reverse chronological order (most recent first),
                truncated if exceeding max_tokens.

        Example:
            >>> belief = Belief()
            >>> def count_tokens(text): return len(text.split())
            >>> belief.update_internal("reasoning", "analysis")
            >>> history = belief.get_internal_history(count_tokens)
            >>> print(history)
            'analysis(reasoning)'
        """
        events = self.get_events_excluding_types([])  # get all events
        results = []
        current_tokens = 0
        for event in reversed(events):
            event_str = str(event)
            results.append(event_str)
            current_tokens += token_counter(event_str)
            if current_tokens > self.max_tokens:
                break
        context = "\n".join(reversed(results))
        return context

    def get_histories_excluding_types(
        self,
        exclude_types: list[str],
        token_counter: Optional[Callable[[str], int]] = None,
        max_tokens=4000,
    ):
        """Get internal history excluding specific event types as a string, with token limiting.

        This method uses get_events_excluding_types to retrieve internal events as dicts (excluding specified types),
        then converts them to strings in reverse order (most recent first) for LLM context, and applies token limiting.

        Args:
            exclude_types (list[str]): List of event types to exclude.
            token_counter (Optional[Callable[[str], int]]): Function to count tokens. If None, uses word count.
            max_tokens (int): Maximum number of tokens in result.

        Returns:
            str: Filtered history string, in reverse chronological order (most recent first),
                truncated if exceeding max_tokens.

        Example:
            >>> belief = Belief()
            >>> def count_tokens(text): return len(text.split())
            >>> belief.update_internal("reasoning", "analysis")
            >>> belief.update_internal("feedback", "comment")
            >>> history = belief.get_histories_excluding_types(["feedback"], count_tokens)
            >>> print(history)
            'analysis(reasoning)'
        """  # noqa: E501
        if token_counter is None:
            def token_counter(x):
                return len(x.split())
        events = self.get_events_excluding_types(exclude_types)
        results = []
        current_tokens = 0
        for event in reversed(events):
            event_str = str(event)
            results.append(event_str)
            current_tokens += token_counter(event_str)
            if current_tokens > max_tokens:
                break
        context = "\n".join(reversed(results))
        return context

    def clear_short_term_memory(self):
        """Clear short-term memory by removing all internal events and dictionary data.

        Example:
            >>> belief = Belief()
            >>> belief.update_internal("reasoning", "analysis")
            >>> belief.set("key", "value")
            >>> belief.clear_short_term_memory()
            >>> print(len(belief.internal_events))
            0
            >>> print(belief.belief_data)
            {}
        """
        self.belief_data.clear()
        self.internal_events.clear()

    def set_actions(self, actions: List[BaseAction]):
        """Set available actions for the agent.

        Args:
            actions (List[BaseAction]): List of actions to make available.

        Example:
            >>> belief = Belief()
            >>> actions = [Action1(), Action2()]
            >>> belief.set_actions(actions)
            >>> print(len(belief.actions))
            2
        """  # noqa: E501
        if self.state_machine is not None:
            logger.warning(
                "State machine exists, please add actions as transitions directly to the state machine"  # noqa: E501
            )
            return

        self.actions = actions

        # TODO: This is a quick an dirty way to set the current task
        # in actions, need to find a better way
        for action in actions:
            if action.__class__.__name__ == "BaseRetrievalAction":
                action.current_task = self.current_task.content

    @property
    def action_description(self):
        """Get string description of all available actions.

        Returns:
            str: Newline-separated string of action descriptions.

        Example:
            >>> belief = Belief()
            >>> belief.set_actions([Action1(), Action2()])
            >>> print(belief.action_description)
            'Action1: Description1\nAction2: Description2'
        """
        return "\n".join([str(action) for action in self.get_actions()])

    def get_state(self) -> str:
        """Get current state name from state machine.

        Returns:
            str: Name of current state, or None if no state machine exists.

        Example:
            >>> belief = Belief()
            >>> belief.state_machine = StateMachine()
            >>> print(belief.get_state())
            'initial'
        """  # noqa: E501
        if self.state_machine is None:
            return None

        return self.state_machine.get_current_state().name

    def get_state_obj(self) -> ts.State:
        """Get current state object from state machine.

        Returns:
            ts.State: Current state object, or None if no state machine exists.

        Example:
            >>> belief = Belief()
            >>> belief.state_machine = StateMachine()
            >>> state = belief.get_state_obj()
            >>> print(state.name)
            'initial'
        """
        if self.state_machine is None:
            return None

        return self.state_machine.get_current_state()

    def get_actions(self) -> List[BaseAction]:
        """Get list of available actions.

        Returns:
            List[BaseAction]: List of available actions.

        Example:
            >>> belief = Belief()
            >>> belief.set_actions([Action1(), Action2()])
            >>> actions = belief.get_actions()
            >>> print(len(actions))
            2
        """
        if self.state_machine is None:
            return self.actions

        return self.state_machine.get_actions()

    def get_action(self, action_name) -> BaseAction:
        """Get specific action by name.

        Args:
            action_name (str): Name of action to retrieve.

        Returns:
            BaseAction: Action with matching name, or None if not found.

        Example:
            >>> belief = Belief()
            >>> belief.set_actions([Action1(name="action1")])
            >>> action = belief.get_action("action1")
            >>> print(action.name)
            'action1'
        """
        if self.state_machine is not None:
            self.actions = self.state_machine.get_actions()

        result = None
        for action in self.actions:
            if action.name == action_name:
                result = action
                break
        return result

    async def async_get_actions(self) -> List[BaseAction]:
        """Asynchronously get list of available actions.

        Returns:
            List[BaseAction]: List of available actions.

        Example:
            >>> belief = Belief()
            >>> belief.set_actions([Action1(), Action2()])
            >>> actions = await belief.async_get_actions()
            >>> print(len(actions))
            2
        """
        if self.state_machine is None:
            return self.actions

        return await self.state_machine.async_get_actions()

    async def async_get_action(self, action_name) -> BaseAction:
        """Asynchronously get specific action by name.

        Args:
            action_name (str): Name of action to retrieve.

        Returns:
            BaseAction: Action with matching name, or None if not found.

        Example:
            >>> belief = Belief()
            >>> belief.set_actions([Action1(name="action1")])
            >>> action = await belief.async_get_action("action1")
            >>> print(action.name)
            'action1'
        """
        if self.state_machine is not None:
            self.actions = await self.state_machine.async_get_actions()

        result = None
        for action in self.actions:
            if action.name == action_name:
                result = action
                break
        return result

    def get_dict(self):
        """Get the belief dictionary.

        Returns:
            dict: Dictionary containing belief data.

        Example:
            >>> belief = Belief()
            >>> belief.set("key", "value")
            >>> print(belief.get_dict())
            {'key': 'value'}
        """
        return self.belief_data

    def get(self, key, default=None):
        """Get value from belief dictionary using dot notation.

        Args:
            key (str): Key to retrieve, can use dot notation for nested values.
            default (Any): Default value if key not found.

        Returns:
            Any: Value at key, or default if not found.

        Example:
            >>> belief = Belief()
            >>> belief.set("nested.key", "value")
            >>> print(belief.get("nested.key"))
            'value'
            >>> print(belief.get("missing.key", "default"))
            'default'
        """
        return pydash.get(self.belief_data, key, default)

    def get_all_keys(self):
        """Get all keys in belief dictionary, including nested keys.

        Returns:
            List[str]: List of all keys, using dot notation for nested keys.

        Example:
            >>> belief = Belief()
            >>> belief.set("nested.key", "value")
            >>> print(belief.get_all_keys())
            ['nested.key']
        """

        def get_all_keys(d, parent_key=""):
            keys = []
            for k, v in d.items():
                full_key = parent_key + "." + k if parent_key else k
                keys.append(full_key)
                if isinstance(v, dict):
                    keys.extend(get_all_keys(v, full_key))
            return keys

        return get_all_keys(self.belief_data)

    def has(self, key):
        """Check if key exists in belief dictionary.

        Args:
            key (str): Key to check, can use dot notation for nested values.

        Returns:
            bool: True if key exists, False otherwise.

        Example:
            >>> belief = Belief()
            >>> belief.set("key", "value")
            >>> print(belief.has("key"))
            True
            >>> print(belief.has("missing.key"))
            False
        """
        return pydash.has(self.belief_data, key)

    def set(self, key, value):
        """Set value in belief dictionary using dot notation.

        Args:
            key (str): Key to set, can use dot notation for nested values.
            value (Any): Value to store.

        Example:
            >>> belief = Belief()
            >>> belief.set("nested.key", "value")
            >>> print(belief.get("nested.key"))
            'value'
        """
        pydash.set_(self.belief_data, key, value)
