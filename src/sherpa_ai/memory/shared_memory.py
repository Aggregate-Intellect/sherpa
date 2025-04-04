from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from sherpa_ai.events import Event, build_event
from sherpa_ai.memory.belief import Belief

if TYPE_CHECKING:
    from sherpa_ai.actions.planning import Plan
    from sherpa_ai.agents import AgentPool


class SharedMemory:
    def __init__(self, objective: str, agent_pool: AgentPool = None):
        self.objective = objective
        self.agent_pool = agent_pool
        self.events: List[Event] = []
        self.plan: Optional[Plan] = None
        self.current_step = None

    def add_event(self, event: Event):
        self.events.append(event)

    def add(self, event_type: str, name: str, **kwargs):
        event = build_event(event_type, name, **kwargs)
        self.add_event(event)

    def observe(self, belief: Belief):
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
        return [event for event in self.events if event.event_type == event_type]

    @property
    def __dict__(self):
        return {
            "objective": self.objective,
            "events": [event.__dict__ for event in self.events],
            "plan": self.plan.__dict__ if self.plan else None,
            "current_step": self.current_step.__dict__ if self.current_step else None,
        }