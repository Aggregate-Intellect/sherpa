from typing import Any, Dict, List, Optional, Union

from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.agents.persistent_agent_pool import PersistentAgentPool
from sherpa_ai.agents.user_agent_manager import UserAgentManager


class AgentPool:
    """A collection of agents that can be managed and accessed by name.

    This class provides a centralized registry for agents, allowing them to be
    added, retrieved, and listed. It maintains a dictionary of agents indexed
    by their names for easy access.

    The AgentPool now supports both in-memory and persistent storage modes.
    When persistent=True, it uses PersistentAgentPool for database-backed storage.
    When user_management=True, it uses UserAgentManager for user-specific agent management.

    Attributes:
        agents (Dict[str, BaseAgent]): Dictionary mapping agent names to agent instances.
        persistent_pool (Optional[PersistentAgentPool]): Persistent agent pool if enabled.
        user_manager (Optional[UserAgentManager]): User agent manager if enabled.

    Example:
        >>> from sherpa_ai.agents.agent_pool import AgentPool
        >>> from sherpa_ai.agents.qa_agent import QAAgent
        >>> # In-memory mode (default)
        >>> pool = AgentPool()
        >>> agent = QAAgent(name="Research Assistant")
        >>> pool.add_agent(agent)
        >>> print("Research Assistant" in pool)
        True
        
        >>> # Persistent mode
        >>> persistent_pool = AgentPool(persistent=True, db_path="agents.db")
        >>> persistent_pool.save_agent(agent, user_id="user123")
        
        >>> # User management mode
        >>> user_pool = AgentPool(user_management=True, db_path="user_agents.db")
        >>> user_pool.create_agent_for_user("user123", "My Assistant", "QAAgent")
    """
    def __init__(self, persistent: bool = False, user_management: bool = False, 
                 db_path: str = "agent_pool.db"):
        """Initialize an agent pool.

        Args:
            persistent (bool): Whether to use persistent storage.
            user_management (bool): Whether to enable user-specific management.
            db_path (str): Path to the database file for persistent storage.

        Example:
            >>> from sherpa_ai.agents.agent_pool import AgentPool
            >>> pool = AgentPool()
            >>> print(len(pool.agents))
            0
        """
        self.agents: Dict[str, BaseAgent] = {}
        self.persistent_pool: Optional[PersistentAgentPool] = None
        self.user_manager: Optional[UserAgentManager] = None
        
        if user_management:
            self.user_manager = UserAgentManager(db_path)
        elif persistent:
            self.persistent_pool = PersistentAgentPool(db_path)

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
    
    # Persistent storage methods
    def save_agent(self, agent: BaseAgent, user_id: str = "default", 
                   tags: List[str] = None, overwrite: bool = False) -> Optional[str]:
        """Save an agent to persistent storage.
        
        Args:
            agent (BaseAgent): The agent to save.
            user_id (str): User ID for the agent.
            tags (List[str]): Tags for categorization.
            overwrite (bool): Whether to overwrite existing agent with same name.
            
        Returns:
            Optional[str]: The agent ID of the saved agent, or None if not in persistent mode.
            
        Example:
            >>> pool = AgentPool(persistent=True)
            >>> agent = QAAgent(name="My Agent")
            >>> agent_id = pool.save_agent(agent, user_id="user123")
            >>> print(agent_id)
            My Agent_140123456789
        """
        if self.persistent_pool:
            return self.persistent_pool.save_agent(agent, user_id, tags, overwrite)
        elif self.user_manager:
            return self.user_manager.agent_pool.save_agent(agent, user_id, tags, overwrite)
        else:
            return None
    
    def get_agent_by_id(self, agent_id: str) -> Optional[BaseAgent]:
        """Retrieve an agent by its ID from persistent storage.
        
        Args:
            agent_id (str): The agent ID to retrieve.
            
        Returns:
            Optional[BaseAgent]: The agent if found, None otherwise.
        """
        if self.persistent_pool:
            return self.persistent_pool.get_agent(agent_id)
        elif self.user_manager:
            return self.user_manager.agent_pool.get_agent(agent_id)
        else:
            return None
    
    def list_agents(self, user_id: str = None, agent_type: str = None, 
                   tags: List[str] = None, active_only: bool = True):
        """List agents with optional filtering.
        
        Args:
            user_id (str): Filter by user ID.
            agent_type (str): Filter by agent type.
            tags (List[str]): Filter by tags (any match).
            active_only (bool): Only return active agents.
            
        Returns:
            List of agent metadata or empty list if not in persistent mode.
        """
        if self.persistent_pool:
            return self.persistent_pool.list_agents(user_id, agent_type, tags, active_only)
        elif self.user_manager:
            return self.user_manager.agent_pool.list_agents(user_id, agent_type, tags, active_only)
        else:
            return []
    
    def delete_agent(self, agent_id: str, soft_delete: bool = True) -> bool:
        """Delete an agent from persistent storage.
        
        Args:
            agent_id (str): The agent ID to delete.
            soft_delete (bool): If True, mark as inactive; if False, permanently delete.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if self.persistent_pool:
            return self.persistent_pool.delete_agent(agent_id, soft_delete)
        elif self.user_manager:
            return self.user_manager.agent_pool.delete_agent(agent_id, soft_delete)
        else:
            return False
    
    def update_agent(self, agent_id: str, agent: BaseAgent) -> bool:
        """Update an existing agent in persistent storage.
        
        Args:
            agent_id (str): The agent ID to update.
            agent (BaseAgent): The updated agent.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if self.persistent_pool:
            return self.persistent_pool.update_agent(agent_id, agent)
        elif self.user_manager:
            return self.user_manager.agent_pool.update_agent(agent_id, agent)
        else:
            return False
    
    # User management methods
    def create_user(self, user_id: str, **preferences):
        """Create a new user with preferences.
        
        Args:
            user_id (str): Unique user identifier.
            **preferences: User preference overrides.
            
        Returns:
            User preferences if user management enabled, None otherwise.
        """
        if self.user_manager:
            return self.user_manager.create_user(user_id, **preferences)
        else:
            return None
    
    def create_agent_for_user(self, user_id: str, agent_name: str, 
                             agent_type: str = None, **kwargs) -> Optional[str]:
        """Create a new agent for a specific user.
        
        Args:
            user_id (str): User identifier.
            agent_name (str): Name for the new agent.
            agent_type (str): Type of agent to create.
            **kwargs: Additional agent configuration.
            
        Returns:
            Optional[str]: Agent ID if successful, None otherwise.
        """
        if self.user_manager:
            return self.user_manager.create_agent_for_user(user_id, agent_name, agent_type, **kwargs)
        else:
            return None
    
    def get_user_agents(self, user_id: str, active_only: bool = True):
        """Get all agents for a specific user.
        
        Args:
            user_id (str): User identifier.
            active_only (bool): Only return active agents.
            
        Returns:
            List of agent metadata or empty list if user management not enabled.
        """
        if self.user_manager:
            return self.user_manager.get_user_agents(user_id, active_only)
        else:
            return []
    
    def get_agent_for_user(self, user_id: str, agent_name: str) -> Optional[BaseAgent]:
        """Get a specific agent for a user.
        
        Args:
            user_id (str): User identifier.
            agent_name (str): Agent name.
            
        Returns:
            Optional[BaseAgent]: The agent if found, None otherwise.
        """
        if self.user_manager:
            return self.user_manager.get_agent_for_user(user_id, agent_name)
        else:
            return None
    
    def start_user_session(self, user_id: str, agent_name: str) -> Optional[str]:
        """Start a new user session with an agent.
        
        Args:
            user_id (str): User identifier.
            agent_name (str): Agent name to use.
            
        Returns:
            Optional[str]: Session ID if successful, None otherwise.
        """
        if self.user_manager:
            return self.user_manager.start_user_session(user_id, agent_name)
        else:
            return None
    
    def end_user_session(self, session_id: str) -> bool:
        """End a user session.
        
        Args:
            session_id (str): Session identifier.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if self.user_manager:
            return self.user_manager.end_user_session(session_id)
        else:
            return False
    
    def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get statistics for a user.
        
        Args:
            user_id (str): User identifier.
            
        Returns:
            Dict[str, Any]: User statistics or empty dict if user management not enabled.
        """
        if self.user_manager:
            return self.user_manager.get_user_statistics(user_id)
        else:
            return {}
