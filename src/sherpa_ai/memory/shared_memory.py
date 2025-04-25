"""Shared memory management module for Sherpa AI.

This module provides shared memory functionality for the Sherpa AI system.
It defines the SharedMemory class which manages shared state between agents.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from sherpa_ai.events import Event, build_event
from sherpa_ai.memory.belief import Belief

if TYPE_CHECKING:
    from sherpa_ai.actions.planning import Plan
    from sherpa_ai.agents import AgentPool


class SharedMemory:
    """Manages shared memory between agents in the Sherpa AI system.

    This class maintains a shared state that can be accessed and modified by multiple agents.
    It tracks events, plans, and current execution steps, providing methods for adding events
    and synchronizing state with agent beliefs.

    Attributes:
        objective (str): The overall objective being pursued.
        agent_pool (AgentPool): Pool of agents that share this memory.
        events (List[Event]): List of events in shared memory.
        plan (Optional[Plan]): Current execution plan.
        current_step: Current step in the execution plan.

    Example:
        >>> memory = SharedMemory("Complete the task")
        >>> memory.add("task", "initial_task", content="Process data")
        >>> belief = Belief()
        >>> memory.observe(belief)
        >>> print(belief.current_task.content)
        'Process data'
    """

    def __init__(self, objective: str, agent_pool: AgentPool = None):
        """Initialize shared memory with an objective.

        Args:
            objective (str): The overall objective to pursue.
            agent_pool (AgentPool, optional): Pool of agents sharing this memory.

        Example:
            >>> memory = SharedMemory("Complete the task")
            >>> print(memory.objective)
            'Complete the task'
        """
        self.objective = objective
        self.agent_pool = agent_pool
        self.events: List[Event] = []
        self.plan: Optional[Plan] = None
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

    def observe(self, belief: Belief):
        """Synchronize agent belief with shared memory state.

        Updates the agent's belief with the current task and relevant events
        from shared memory.

        Args:
            belief (Belief): Agent belief to update.

        Example:
            >>> memory = SharedMemory("Complete the task")
            >>> memory.add("task", "initial_task", content="Process data")
            >>> belief = Belief()
            >>> memory.observe(belief)
            >>> print(belief.current_task.content)
            'Process data'
        """
        tasks = self.get_by_type("task")
        task = tasks[-1] if len(tasks) > 0 else None

        belief.set_current_task(task.content)

        for event in self.events:
            if (
                event.event_type == "task"
                or event.event_type == "result"
            ):
                belief.update(event)

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

    @property
    def __dict__(self):
        """Get dictionary representation of shared memory state.

        Returns:
            dict: Dictionary containing objective, events, plan, and current step.

        Example:
            >>> memory = SharedMemory("Complete the task")
            >>> memory.add("task", "initial_task", content="Process data")
            >>> print(memory.__dict__)
            {'objective': 'Complete the task', 'events': [...], 'plan': None, 'current_step': None}
        """
        return {
            "objective": self.objective,
            "events": [event.__dict__ for event in self.events],
            "plan": self.plan.__dict__ if self.plan else None,
            "current_step": self.current_step.__dict__ if self.current_step else None,
        }