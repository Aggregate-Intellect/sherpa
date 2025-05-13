from typing import Dict, List, Optional

from sherpa_ai.agents.base import BaseAgent


class AgentPool:
    """A collection of agents that can be managed and accessed by name.

    This class provides a centralized registry for agents, allowing them to be
    added, retrieved, and listed. It maintains a dictionary of agents indexed
    by their names for easy access.

    Attributes:
        agents (Dict[str, BaseAgent]): Dictionary mapping agent names to agent instances.

    Example:
        >>> from sherpa_ai.agents.agent_pool import AgentPool
        >>> from sherpa_ai.agents.qa_agent import QAAgent
        >>> pool = AgentPool()
        >>> agent = QAAgent(name="Research Assistant")
        >>> pool.add_agent(agent)
        >>> print("Research Assistant" in pool)
        True
    """
    def __init__(self):
        """Initialize an empty agent pool.

        Example:
            >>> from sherpa_ai.agents.agent_pool import AgentPool
            >>> pool = AgentPool()
            >>> print(len(pool.agents))
            0
        """
        self.agents: Dict[str, BaseAgent] = {}

    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """Retrieve an agent by its name.

        Args:
            agent_name (str): The name of the agent to retrieve.

        Returns:
            Optional[BaseAgent]: The agent with the specified name, or None if not found.

        Example:
            >>> from sherpa_ai.agents.agent_pool import AgentPool
            >>> from sherpa_ai.agents.qa_agent import QAAgent
            >>> pool = AgentPool()
            >>> agent = QAAgent(name="Research Assistant")
            >>> pool.add_agent(agent)
            >>> retrieved = pool.get_agent("Research Assistant")
            >>> print(retrieved.name)
            Research Assistant
        """
        return self.agents.get(agent_name, None)

    def __contains__(self, agent_name: str) -> bool:
        """Check if an agent with the given name exists in the pool.

        Args:
            agent_name (str): The name of the agent to check for.

        Returns:
            bool: True if the agent exists in the pool, False otherwise.

        Example:
            >>> from sherpa_ai.agents.agent_pool import AgentPool
            >>> from sherpa_ai.agents.qa_agent import QAAgent
            >>> pool = AgentPool()
            >>> agent = QAAgent(name="Research Assistant")
            >>> pool.add_agent(agent)
            >>> print("Research Assistant" in pool)
            True
            >>> print("Unknown Agent" in pool)
            False
        """
        return agent_name in self.agents

    def add_agent(self, agent: BaseAgent):
        """Add a single agent to the pool.

        Args:
            agent (BaseAgent): The agent to add to the pool.

        Example:
            >>> from sherpa_ai.agents.agent_pool import AgentPool
            >>> from sherpa_ai.agents.qa_agent import QAAgent
            >>> pool = AgentPool()
            >>> agent = QAAgent(name="Research Assistant")
            >>> pool.add_agent(agent)
            >>> print(len(pool.agents))
            1
        """
        self.agents[agent.name] = agent

    def add_agents(self, agents: List[BaseAgent]):
        """Add multiple agents to the pool.

        Args:
            agents (List[BaseAgent]): List of agents to add to the pool.

        Example:
            >>> from sherpa_ai.agents.agent_pool import AgentPool
            >>> from sherpa_ai.agents.qa_agent import QAAgent
            >>> from sherpa_ai.agents.ml_engineer import MLEngineer
            >>> pool = AgentPool()
            >>> agents = [
            ...     QAAgent(name="Research Assistant"),
            ...     MLEngineer(name="AI Expert")
            ... ]
            >>> pool.add_agents(agents)
            >>> print(len(pool.agents))
            2
        """
        for agent in agents:
            self.add_agent(agent)

    def get_agent_pool_description(self) -> str:
        """Create a description of all agents in the pool.

        This method generates a formatted string containing the name and description
        of each agent in the pool, which can be used for agent planning or display.

        Returns:
            str: A formatted string describing all agents in the pool.

        Example:
            >>> from sherpa_ai.agents.agent_pool import AgentPool
            >>> from sherpa_ai.agents.qa_agent import QAAgent
            >>> pool = AgentPool()
            >>> agent = QAAgent(name="Research Assistant")
            >>> pool.add_agent(agent)
            >>> description = pool.get_agent_pool_description()
            >>> print("Research Assistant" in description)
            True
        """
        result = ""

        for name, agent in self.agents.items():
            result += f"Agent: {name}.\n Description: {agent.description}\n\n"

        return result
