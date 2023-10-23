from typing import Dict, List, Optional

from sherpa_ai.agents.base import BaseAgent


class AgentPool:
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}

    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """
        Get agent by name
        """
        return self.agents.get(agent_name, None)

    def __contains__(self, agent_name: str) -> bool:
        """
        Check if agent pool contains agent
        """
        return agent_name in self.agents

    def add_agent(self, agent: BaseAgent):
        """
        Add agent to agent pool
        """
        self.agents[agent.name] = agent

    def add_agents(self, agents: List[BaseAgent]):
        """
        Add agents to agent pool
        """
        for agent in agents:
            self.add_agent(agent)

    def get_agent_pool_description(self) -> str:
        """
        Create a description (prompt) of the AgentPool for agent planning
        """
        result = ""

        for name, agent in self.agents.items():
            result += f"Agent: {name}.\n Description: {agent.description}\n\n"

        return result
