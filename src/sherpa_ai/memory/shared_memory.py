from typing import List

from sherpa_ai.agents import AgentPool
from sherpa_ai.memory.events import Event


class SharedMemory:
    def __init__(self, objective: str, agent_pool: AgentPool, events: List[Event]):
        # TODO: Maybe consider vector database if necessary
        pass

    def observe(self, belief):
        pass
