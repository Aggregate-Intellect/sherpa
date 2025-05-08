"""Shared memory management module for Sherpa AI.

This module provides shared memory functionality for the Sherpa AI system.
It defines the SharedMemory class which manages shared state between agents.
"""

from __future__ import annotations

from typing import List

from sherpa_ai.events import Event, build_event


class SharedMemory:
    """Manages shared memory between agents in the Sherpa AI system.

    This class maintains a shared state that can be accessed and modified by multiple agents.
    It tracks events, plans, and current execution steps, providing methods for adding events
    and synchronizing state with agent beliefs.

    Attributes:
        objective (str): The overall objective being pursued.
        events (List[Event]): List of events in shared memory.
        plan (Optional[Plan]): Current execution plan.
        current_step: Current step in the execution plan.

    """  # noqa: E501

    def __init__(self, objective: str):
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
        self.current_step = None

    def add_event(self, event: Event):
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
        self.events.append(event)

    def add(self, event_type: str, name: str, **kwargs):
        """Create and add an event to shared memory.

        Args:
            event_type (str): Type of the event.
            name (str): Name of the event.
            **kwargs: Additional event parameters.

        Example:
            >>> memory = SharedMemory("Complete the task")
            >>> memory.add("task", "initial_task", content="Process data")
            >>> print(memory.events[0].event_type)
            'task'
        """
        event = build_event(event_type, name, **kwargs)
        self.add_event(event)

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
