"""Shared memory management module for Sherpa AI.

This module provides shared memory functionality for the Sherpa AI system.
It defines the SharedMemory class which manages shared state between agents.
"""

from __future__ import annotations

import asyncio
import threading
from typing import TYPE_CHECKING, List

from sherpa_ai.events import Event, build_event

if TYPE_CHECKING:
    from sherpa_ai.agents.base import BaseAgent


class SharedMemory:
    """Manages shared memory between agents in the Sherpa AI system.

    This class maintains a shared state that can be accessed and modified by multiple agents.
    It tracks events, plans, and current execution steps, providing methods for adding events
    and synchronizing state with agent beliefs. Note that the agent names registered in the shared
    memory must be unique

    Attributes:
        objective (str): The overall objective being pursued.
        events (List[Event]): List of events in shared memory.
        event_type_subscriptions (dict[type[Event], list[BaseAgent]]): Agent subscriptions to specific event types.
        sender_subscriptions (dict[str, list[BaseAgent]]): Agent subscriptions based on sender.
        _lock (threading.RLock): Reentrant lock for thread safety.

    """  # noqa: E501

    def __init__(self, objective: str = ""):
        """Initialize shared memory with an objective.

        Args:
            objective (str): The overall objective to pursue.

        Example:
            >>> memory = SharedMemory("Complete the task")
            >>> print(memory.objective)
            'Complete the task'
        """
        self.objective = objective
        self.events: List[Event] = []
        self.event_type_subscriptions: dict[type[Event], list[BaseAgent]] = {}
        self.sender_subscriptions: dict[str, list[BaseAgent]] = {}
        self._lock = threading.RLock()

    async def add_event(self, event: Event):
        """Add an event to shared memory.

        Args:
            event (Event): Event to add to shared memory.

        Example:
            >>> memory = SharedMemory("Complete the task")
            >>> event = Event("task", "initial_task", "Process data")
            >>> memory.add_event(event)
            >>> print(len(memory.events))
            1
        """
        # List to store all handler coroutines
        processed_agent = set()

        with self._lock:
            # Add event to the list
            self.events.append(event)

            # Collect handler tasks for event type subscribers
            if event.event_type in self.event_type_subscriptions:
                for agent in self.event_type_subscriptions[event.event_type]:
                    processed_agent.add(agent)

            # Collect handler tasks for sender subscribers
            if event.sender in self.sender_subscriptions:
                for agent in self.sender_subscriptions[event.sender]:
                    processed_agent.add(agent)

        # Execute all handlers in parallel (outside the lock to prevent deadlocks)
        if processed_agent:
            handler_tasks = [
                agent.async_handle_event(event) for agent in processed_agent
            ]
            await asyncio.gather(*handler_tasks)

    def add(self, event_type: str, name: str, sender="", **kwargs):
        asyncio.run(self.async_add(event_type, name, sender, **kwargs))

    async def async_add(self, event_type: str, name: str, sender="", **kwargs):
        """Create and add an event to shared memory.

        Args:
            event_type (str): Type of the event.
            name (str): Name of the event.
            **kwargs: Additional event parameters.
        """
        event = build_event(event_type, name, sender=sender, **kwargs)
        await self.add_event(event)

    def subscribe_event_type(self, event_type: str, agent: BaseAgent):
        """Subscribe an agent to a specific event type.
        Args:
            event_type (str): Type of event to subscribe to.
            agent (BaseAgent): Agent subscribing to the event type.

        Example:
            >>> memory = SharedMemory("Complete the task")
            >>> agent = BaseAgent()
            >>> memory.subscribe("trigger", agent)
            >>> print(len(memory.event_type_subscriptions))
            1
        """
        with self._lock:
            if event_type not in self.event_type_subscriptions:
                self.event_type_subscriptions[event_type] = []
            self.event_type_subscriptions[event_type].append(agent)

    def subscribe_sender(self, sender: str, agent: BaseAgent):
        """Subscribe an agent to events from a specific sender.

        Args:
            sender (str): Sender of the events.
            agent (BaseAgent): Agent subscribing to the sender.

        Example:
            >>> memory = SharedMemory("Complete the task")
            >>> agent = BaseAgent()
            >>> memory.subscribe_sender("agent1", agent)
            >>> print(len(memory.sender_subscriptions))
            1
        """
        with self._lock:
            if sender not in self.sender_subscriptions:
                self.sender_subscriptions[sender] = []
            self.sender_subscriptions[sender].append(agent)

    def get_by_type(self, event_type):
        """Get all events of a specific type.

        Args:
            event_type (str): Type of events to retrieve.

        Returns:
            List[Event]: List of events matching the type.

        Example:
            >>> memory = SharedMemory("Complete the task")
            >>> memory.add("task", "task1", content="First task")
            >>> memory.add("task", "task2", content="Second task")
            >>> tasks = memory.get_by_type("task")
            >>> print(len(tasks))
            2
        """
        return [event for event in self.events if event.event_type == event_type]
