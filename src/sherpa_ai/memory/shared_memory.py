"""Shared memory management module for Sherpa AI.

This module provides shared memory functionality for the Sherpa AI system.
It defines the SharedMemory class which manages shared state between agents.
"""

from __future__ import annotations

import asyncio
import threading
from typing import List

from sherpa_ai.events import Event, build_event
from sherpa_ai.runtime import ThreadedRuntime


class SharedMemory:
    """Manages shared memory between agents in the Sherpa AI system.

    This class maintains a shared state that can be accessed and modified by multiple agents.
    It tracks events, plans, and current execution steps, providing methods for adding events
    and synchronizing state with agent beliefs. Note that the agent names registered in the shared
    memory must be unique

    Attributes:
        objective (str): The overall objective being pursued.
        events (List[Event]): List of events in shared memory.
        event_type_subscriptions (dict[type[Event], list[ThreadedRuntime]]): Agent runtime subscriptions to specific event types.
        sender_subscriptions (dict[str, list[ThreadedRuntime]]): Agent runtime subscriptions based on sender.
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
        self.event_type_subscriptions: dict[type[Event], list[ThreadedRuntime]] = {}
        self.sender_subscriptions: dict[str, list[ThreadedRuntime]] = {}
        self._lock = threading.RLock()

    async def add_event(self, event: Event, wait: bool = False):
        """Add an event to shared memory.

        Args:
            event (Event): Event to add to shared memory.
            wait (bool): Whether to wait for the event to be processed.

        Example:
            >>> memory = SharedMemory("Complete the task")
            >>> event = Event("task", "initial_task", "Process data")
            >>> memory.add_event(event)
            >>> print(len(memory.events))
            1
        """
        # List to store all handler coroutines
        processed_subscribers = set()

        with self._lock:
            # Add event to the list
            self.events.append(event)

            # Collect handler tasks for event type subscribers
            if event.event_type in self.event_type_subscriptions:
                for subscriber in self.event_type_subscriptions[event.event_type]:
                    processed_subscribers.add(subscriber)

            # Collect handler tasks for sender subscribers
            if event.sender in self.sender_subscriptions:
                for subscriber in self.sender_subscriptions[event.sender]:
                    processed_subscribers.add(subscriber)

        # send event to all subscribers
        for subscriber in processed_subscribers:
            subscriber.ask(event, block=wait)

    def add(self, event_type: str, name: str, sender="", **kwargs):
        asyncio.run(self.async_add(event_type, name, sender, **kwargs))

    async def async_add(
        self, event_type: str, name: str, sender="", wait: bool = False, **kwargs
    ):
        """Create and add an event to shared memory.

        Args:
            event_type (str): Type of the event.
            name (str): Name of the event.
            sender (str): Sender of the event.
            wait (bool): Whether to wait for the event to be processed.
            **kwargs: Additional event parameters.
        """
        event = build_event(event_type, name, sender=sender, **kwargs)
        await self.add_event(event, wait=wait)

    def subscribe_event_type(self, event_type: str, subscriber: ThreadedRuntime):
        """Subscribe an agent to a specific event type.
        Args:
            event_type (str): Type of event to subscribe to.
            subscriber (ThreadedRuntime): Agent runtime subscribing to the event type.

        Example:
            >>> memory = SharedMemory("Complete the task")
            >>> runtime = ThreadedRuntime(QAAgent())
            >>> memory.subscribe("trigger", runtime)
            >>> print(len(memory.event_type_subscriptions))
            1
        """
        with self._lock:
            if event_type not in self.event_type_subscriptions:
                self.event_type_subscriptions[event_type] = []
            self.event_type_subscriptions[event_type].append(subscriber)

    def subscribe_sender(self, sender: str, subscriber: ThreadedRuntime):
        """Subscribe an agent to events from a specific sender.

        Args:
            sender (str): Sender of the events.
            subscriber (ThreadedRuntime): Agent runtime subscribing to the sender.

        Example:
            >>> memory = SharedMemory("Complete the task")
            >>> subscriber = ThreadedRuntime(QAAgent())
            >>> memory.subscribe_sender("agent1", runtime)
            >>> print(len(memory.sender_subscriptions))
            1
        """
        with self._lock:
            if sender not in self.sender_subscriptions:
                self.sender_subscriptions[sender] = []
            self.sender_subscriptions[sender].append(subscriber)

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
