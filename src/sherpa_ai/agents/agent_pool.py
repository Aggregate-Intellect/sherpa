from typing import List

from sherpa_ai.agents.base import BaseAgent


class AgentPool:
    def __init__(self, agents: List[BaseAgent]):
        self.agents = {agent.name for agent in agents}

    def get_agent(self, agent_name: str) -> BaseAgent:
        """
        Get agent by name
        """
        raise NotImplementedError

    def get_agent_pool_description(self) -> str:
        """
        Create a description (prompt) of the AgentPool for agent planning
        """
        raise NotImplementedError
