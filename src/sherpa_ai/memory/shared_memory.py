from typing import List

from sherpa_ai.agents import AgentPool
from sherpa_ai.memory.belief import Belief
from sherpa_ai.memory.events import Event, EventType


class SharedMemory:
    def __init__(self, objective: str, agent_pool: AgentPool):
        self.objective = objective
        self.agent_pool = agent_pool
        self.events: List[Event] = []
        self.plan = None
        self.current_step = None

    def add_event(self, event: Event):
        self.events.append(event)

    def add(self, event_type: EventType, agent: str, content: str):
        event = Event(event_type=event_type, agent=agent, content=content)
        self.add_event(event)

    def observe(self, belief: Belief):
        tasks = self.shared_memory.get_by_type(EventType.task)
        task = tasks[-1] if len(tasks) > 0 else ""

        belief.set_current_task(task)

        for event in self.events:
            if (
                event.event_type == EventType.task
                or event.event_type == EventType.result
            ):
                belief.update(event)

    def get_by_type(self, event_type):
        return [event for event in self.events if event.event_type == event_type]
