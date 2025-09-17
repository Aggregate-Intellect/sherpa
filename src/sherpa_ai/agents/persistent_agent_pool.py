"""Persistent Agent Pool module for Sherpa AI.

This module provides a comprehensive agent persistence and retrieval system that supports
user-specific agent management, state serialization, and database-backed storage.
"""

import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from loguru import logger
from pydantic import BaseModel, Field, ValidationError

from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.agents.agent_serializer import AgentSerializationManager, SerializationContext
from sherpa_ai.memory.belief import Belief


class AgentMetadata(BaseModel):
    """Metadata for agent storage and retrieval.
    
    Attributes:
        agent_id (str): Unique identifier for the agent.
        user_id (str): User who owns this agent.
        agent_name (str): Human-readable name of the agent.
        agent_type (str): Type/class of the agent.
        created_at (datetime): When the agent was created.
        updated_at (datetime): When the agent was last updated.
        is_active (bool): Whether the agent is currently active.
        tags (List[str]): Tags for categorization and search.
        description (str): Description of the agent's purpose.
    """
    
    agent_id: str = Field(..., description="Unique identifier for the agent")
    user_id: str = Field(..., description="User who owns this agent")
    agent_name: str = Field(..., description="Human-readable name of the agent")
    agent_type: str = Field(..., description="Type/class of the agent")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    tags: List[str] = Field(default_factory=list)
    description: str = Field(default="", description="Description of the agent's purpose")


class AgentState(BaseModel):
    """Serializable agent state for persistence.
    
    Attributes:
        agent_config (Dict[str, Any]): Agent configuration data.
        belief_state (Dict[str, Any]): Agent's belief state.
        shared_memory_state (Dict[str, Any]): Shared memory state.
        execution_state (Dict[str, Any]): Current execution state.
    """
    
    agent_config: Dict[str, Any] = Field(default_factory=dict)
    belief_state: Dict[str, Any] = Field(default_factory=dict)
    shared_memory_state: Dict[str, Any] = Field(default_factory=dict)
    execution_state: Dict[str, Any] = Field(default_factory=dict)


class StoredAgent(BaseModel):
    """Complete stored agent representation.
    
    Attributes:
        metadata (AgentMetadata): Agent metadata.
        state (AgentState): Agent state data.
    """
    
    metadata: AgentMetadata
    state: AgentState


class PersistentAgentPool:
    """Enhanced agent pool with persistence and user-specific management.
    
    This class provides a comprehensive agent management system that supports:
    - User-specific agent storage and retrieval
    - Agent state persistence across sessions
    - Pydantic validation for data integrity
    - Database-backed storage with SQLite
    - Thread-safe operations
    - Agent metadata and tagging
    
    Attributes:
        db_path (str): Path to the SQLite database file.
        _lock (threading.RLock): Thread safety lock.
        _cache (Dict[str, BaseAgent]): In-memory agent cache.
    """
    
    def __init__(self, db_path: str = "agent_pool.db"):
        """Initialize the persistent agent pool.
        
        Args:
            db_path (str): Path to the SQLite database file.
            
        Example:
            >>> pool = PersistentAgentPool("my_agents.db")
            >>> print(pool.db_path)
            my_agents.db
        """
        self.db_path = db_path
        self._lock = threading.RLock()
        self._cache: Dict[str, BaseAgent] = {}
        
        # Initialize serializer
        self.serializer = AgentSerializationManager()
        
        # Initialize database
        self._init_database()
        
        # Load agents from database into cache
        self._load_agents_from_db()
    
    def _init_database(self):
        """Initialize the SQLite database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create agents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    agent_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    agent_type TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    tags TEXT,  -- JSON array of tags
                    description TEXT,
                    agent_config TEXT,  -- JSON
                    belief_state TEXT,  -- JSON
                    shared_memory_state TEXT,  -- JSON
                    execution_state TEXT,  -- JSON
                    UNIQUE(user_id, agent_name)
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON agents(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_name ON agents(agent_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_type ON agents(agent_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_is_active ON agents(is_active)")
            
            conn.commit()
    
    def _load_agents_from_db(self):
        """Load all active agents from database into cache."""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT agent_id, agent_config, belief_state, 
                               shared_memory_state, execution_state
                        FROM agents 
                        WHERE is_active = 1
                    """)
                    
                    for row in cursor.fetchall():
                        agent_id, config_json, belief_json, memory_json, exec_json = row
                        
                        try:
                            # Deserialize agent state
                            agent_config = json.loads(config_json) if config_json else {}
                            belief_state = json.loads(belief_json) if belief_json else {}
                            memory_state = json.loads(memory_json) if memory_json else {}
                            exec_state = json.loads(exec_json) if exec_json else {}
                            
                            # Reconstruct agent (this would need to be implemented based on agent type)
                            agent = self._deserialize_agent(agent_config, belief_state, memory_state, exec_state)
                            if agent:
                                self._cache[agent_id] = agent
                                
                        except (json.JSONDecodeError, ValidationError) as e:
                            logger.warning(f"Failed to load agent {agent_id}: {e}")
                            
            except sqlite3.Error as e:
                logger.error(f"Database error while loading agents: {e}")
    
    def _serialize_agent(self, agent: BaseAgent) -> StoredAgent:
        """Serialize an agent to a StoredAgent object.
        
        Args:
            agent (BaseAgent): The agent to serialize.
            
        Returns:
            StoredAgent: Serialized agent data.
        """
        # Create metadata
        metadata = AgentMetadata(
            agent_id=f"{agent.name}_{id(agent)}",  # Simple ID generation
            user_id=getattr(agent, 'user_id', 'default'),
            agent_name=agent.name,
            agent_type=agent.__class__.__name__,
            description=agent.description,
            tags=getattr(agent, 'tags', [])
        )
        
        # Serialize agent configuration using the proper serializer
        agent_config = self.serializer.serialize_agent(agent)
        
        # Serialize belief state
        belief_state = {}
        if hasattr(agent, 'belief') and agent.belief:
            belief_state = agent.belief.model_dump()
        
        # Serialize shared memory state
        memory_state = {}
        if hasattr(agent, 'shared_memory') and agent.shared_memory:
            memory_state = {
                'objective': agent.shared_memory.objective,
                'events': [event.model_dump() for event in agent.shared_memory.events]
            }
        
        # Serialize execution state
        execution_state = {
            'num_runs': getattr(agent, 'num_runs', 1),
            'validation_steps': getattr(agent, 'validation_steps', 1),
            'global_regen_max': getattr(agent, 'global_regen_max', 12)
        }
        
        state = AgentState(
            agent_config=agent_config,
            belief_state=belief_state,
            shared_memory_state=memory_state,
            execution_state=execution_state
        )
        
        return StoredAgent(metadata=metadata, state=state)
    
    def _deserialize_agent(self, config: Dict[str, Any], belief_state: Dict[str, Any], 
                          memory_state: Dict[str, Any], exec_state: Dict[str, Any]) -> Optional[BaseAgent]:
        """Deserialize an agent from stored data.
        
        Args:
            config (Dict[str, Any]): Agent configuration.
            belief_state (Dict[str, Any]): Belief state.
            memory_state (Dict[str, Any]): Shared memory state.
            exec_state (Dict[str, Any]): Execution state.
            
        Returns:
            Optional[BaseAgent]: Deserialized agent or None if failed.
        """
        try:
            # This is a simplified deserialization - in practice, you'd need
            # to handle different agent types and their specific requirements
            agent_type = config.get('agent_type', 'BaseAgent')
            
            # For now, we'll create a basic agent structure
            # In a real implementation, you'd need to import the specific agent class
            # and handle complex object reconstruction (LLM, policies, actions, etc.)
            
            # This is a placeholder - actual implementation would be more complex
            logger.warning(f"Agent deserialization not fully implemented for type: {agent_type}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to deserialize agent: {e}")
            return None
    
    def save_agent(self, agent: BaseAgent, user_id: str = "default", 
                   tags: List[str] = None, overwrite: bool = False) -> str:
        """Save an agent to persistent storage.
        
        Args:
            agent (BaseAgent): The agent to save.
            user_id (str): User ID for the agent.
            tags (List[str]): Tags for categorization.
            overwrite (bool): Whether to overwrite existing agent with same name.
            
        Returns:
            str: The agent ID of the saved agent.
            
        Raises:
            ValueError: If agent with same name exists and overwrite is False.
            
        Example:
            >>> pool = PersistentAgentPool()
            >>> agent = QAAgent(name="My Agent")
            >>> agent_id = pool.save_agent(agent, user_id="user123", tags=["qa", "research"])
            >>> print(agent_id)
            My Agent_140123456789
        """
        with self._lock:
            try:
                # Check if agent with same name exists for this user
                if not overwrite:
                    existing = self.get_agent_by_name(agent.name, user_id)
                    if existing:
                        raise ValueError(f"Agent '{agent.name}' already exists for user '{user_id}'. Use overwrite=True to replace.")
                
                # Set user_id and tags on agent
                agent.user_id = user_id
                agent.tags = tags or []
                
                # Serialize agent
                stored_agent = self._serialize_agent(agent)
                agent_id = stored_agent.metadata.agent_id
                
                # Save to database
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Delete existing agent if overwriting
                    if overwrite:
                        cursor.execute("DELETE FROM agents WHERE user_id = ? AND agent_name = ?", 
                                     (user_id, agent.name))
                    
                    # Insert new agent
                    cursor.execute("""
                        INSERT INTO agents (
                            agent_id, user_id, agent_name, agent_type, created_at, updated_at,
                            is_active, tags, description, agent_config, belief_state,
                            shared_memory_state, execution_state
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        agent_id,
                        user_id,
                        agent.name,
                        agent.__class__.__name__,
                        stored_agent.metadata.created_at.isoformat(),
                        stored_agent.metadata.updated_at.isoformat(),
                        stored_agent.metadata.is_active,
                        json.dumps(stored_agent.metadata.tags),
                        stored_agent.metadata.description,
                        json.dumps(stored_agent.state.agent_config),
                        json.dumps(stored_agent.state.belief_state),
                        json.dumps(stored_agent.state.shared_memory_state),
                        json.dumps(stored_agent.state.execution_state)
                    ))
                    
                    conn.commit()
                
                # Add to cache
                self._cache[agent_id] = agent
                
                logger.info(f"Saved agent '{agent.name}' with ID '{agent_id}' for user '{user_id}'")
                return agent_id
                
            except Exception as e:
                logger.error(f"Failed to save agent '{agent.name}': {e}")
                raise
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Retrieve an agent by its ID.
        
        Args:
            agent_id (str): The agent ID to retrieve.
            
        Returns:
            Optional[BaseAgent]: The agent if found, None otherwise.
            
        Example:
            >>> pool = PersistentAgentPool()
            >>> agent = pool.get_agent("My Agent_140123456789")
            >>> print(agent.name if agent else "Not found")
            My Agent
        """
        with self._lock:
            # Check cache first
            if agent_id in self._cache:
                return self._cache[agent_id]
            
            # Load from database
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT agent_config, belief_state, shared_memory_state, execution_state
                        FROM agents 
                        WHERE agent_id = ? AND is_active = 1
                    """, (agent_id,))
                    
                    row = cursor.fetchone()
                    if row:
                        config_json, belief_json, memory_json, exec_json = row
                        
                        agent_config = json.loads(config_json) if config_json else {}
                        belief_state = json.loads(belief_json) if belief_json else {}
                        memory_state = json.loads(memory_json) if memory_json else {}
                        exec_state = json.loads(exec_json) if exec_json else {}
                        
                        agent = self._deserialize_agent(agent_config, belief_state, memory_state, exec_state)
                        if agent:
                            self._cache[agent_id] = agent
                            return agent
                            
            except (sqlite3.Error, json.JSONDecodeError) as e:
                logger.error(f"Failed to load agent {agent_id}: {e}")
            
            return None
    
    def get_agent_by_name(self, agent_name: str, user_id: str = "default") -> Optional[BaseAgent]:
        """Retrieve an agent by name and user ID.
        
        Args:
            agent_name (str): The agent name to retrieve.
            user_id (str): The user ID who owns the agent.
            
        Returns:
            Optional[BaseAgent]: The agent if found, None otherwise.
            
        Example:
            >>> pool = PersistentAgentPool()
            >>> agent = pool.get_agent_by_name("My Agent", "user123")
            >>> print(agent.name if agent else "Not found")
            My Agent
        """
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT agent_id FROM agents 
                        WHERE agent_name = ? AND user_id = ? AND is_active = 1
                    """, (agent_name, user_id))
                    
                    row = cursor.fetchone()
                    if row:
                        agent_id = row[0]
                        return self.get_agent(agent_id)
                        
            except sqlite3.Error as e:
                logger.error(f"Failed to find agent '{agent_name}' for user '{user_id}': {e}")
            
            return None
    
    def list_agents(self, user_id: str = None, agent_type: str = None, 
                   tags: List[str] = None, active_only: bool = True) -> List[AgentMetadata]:
        """List agents with optional filtering.
        
        Args:
            user_id (str): Filter by user ID.
            agent_type (str): Filter by agent type.
            tags (List[str]): Filter by tags (any match).
            active_only (bool): Only return active agents.
            
        Returns:
            List[AgentMetadata]: List of agent metadata matching the criteria.
            
        Example:
            >>> pool = PersistentAgentPool()
            >>> agents = pool.list_agents(user_id="user123", tags=["qa"])
            >>> for agent in agents:
            ...     print(f"{agent.agent_name} ({agent.agent_type})")
            My QA Agent (QAAgent)
        """
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Build query
                    query = "SELECT * FROM agents WHERE 1=1"
                    params = []
                    
                    if user_id:
                        query += " AND user_id = ?"
                        params.append(user_id)
                    
                    if agent_type:
                        query += " AND agent_type = ?"
                        params.append(agent_type)
                    
                    if active_only:
                        query += " AND is_active = 1"
                    
                    cursor.execute(query, params)
                    
                    agents = []
                    for row in cursor.fetchall():
                        # Parse tags
                        tags_json = row[7]  # tags column
                        agent_tags = json.loads(tags_json) if tags_json else []
                        
                        # Check tag filter
                        if tags and not any(tag in agent_tags for tag in tags):
                            continue
                        
                        metadata = AgentMetadata(
                            agent_id=row[0],
                            user_id=row[1],
                            agent_name=row[2],
                            agent_type=row[3],
                            created_at=datetime.fromisoformat(row[4]),
                            updated_at=datetime.fromisoformat(row[5]),
                            is_active=bool(row[6]),
                            tags=agent_tags,
                            description=row[8] or ""
                        )
                        agents.append(metadata)
                    
                    return agents
                    
            except (sqlite3.Error, json.JSONDecodeError) as e:
                logger.error(f"Failed to list agents: {e}")
                return []
    
    def delete_agent(self, agent_id: str, soft_delete: bool = True) -> bool:
        """Delete an agent.
        
        Args:
            agent_id (str): The agent ID to delete.
            soft_delete (bool): If True, mark as inactive; if False, permanently delete.
            
        Returns:
            bool: True if successful, False otherwise.
            
        Example:
            >>> pool = PersistentAgentPool()
            >>> success = pool.delete_agent("My Agent_140123456789")
            >>> print("Deleted" if success else "Failed")
            Deleted
        """
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    if soft_delete:
                        cursor.execute("""
                            UPDATE agents SET is_active = 0, updated_at = ?
                            WHERE agent_id = ?
                        """, (datetime.utcnow().isoformat(), agent_id))
                    else:
                        cursor.execute("DELETE FROM agents WHERE agent_id = ?", (agent_id,))
                    
                    conn.commit()
                    
                    # Remove from cache
                    if agent_id in self._cache:
                        del self._cache[agent_id]
                    
                    logger.info(f"Deleted agent {agent_id} (soft_delete={soft_delete})")
                    return True
                    
            except sqlite3.Error as e:
                logger.error(f"Failed to delete agent {agent_id}: {e}")
                return False
    
    def update_agent(self, agent_id: str, agent: BaseAgent) -> bool:
        """Update an existing agent.
        
        Args:
            agent_id (str): The agent ID to update.
            agent (BaseAgent): The updated agent.
            
        Returns:
            bool: True if successful, False otherwise.
            
        Example:
            >>> pool = PersistentAgentPool()
            >>> agent = QAAgent(name="Updated Agent")
            >>> success = pool.update_agent("My Agent_140123456789", agent)
            >>> print("Updated" if success else "Failed")
            Updated
        """
        with self._lock:
            try:
                # Serialize updated agent
                stored_agent = self._serialize_agent(agent)
                
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        UPDATE agents SET
                            agent_name = ?, agent_type = ?, updated_at = ?,
                            tags = ?, description = ?, agent_config = ?,
                            belief_state = ?, shared_memory_state = ?, execution_state = ?
                        WHERE agent_id = ?
                    """, (
                        agent.name,
                        agent.__class__.__name__,
                        datetime.utcnow().isoformat(),
                        json.dumps(stored_agent.metadata.tags),
                        stored_agent.metadata.description,
                        json.dumps(stored_agent.state.agent_config),
                        json.dumps(stored_agent.state.belief_state),
                        json.dumps(stored_agent.state.shared_memory_state),
                        json.dumps(stored_agent.state.execution_state),
                        agent_id
                    ))
                    
                    conn.commit()
                
                # Update cache
                self._cache[agent_id] = agent
                
                logger.info(f"Updated agent {agent_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to update agent {agent_id}: {e}")
                return False
    
    def get_agent_count(self, user_id: str = None) -> int:
        """Get the count of agents.
        
        Args:
            user_id (str): Count agents for specific user, or all if None.
            
        Returns:
            int: Number of active agents.
            
        Example:
            >>> pool = PersistentAgentPool()
            >>> count = pool.get_agent_count("user123")
            >>> print(f"User has {count} agents")
            User has 5 agents
        """
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    if user_id:
                        cursor.execute("SELECT COUNT(*) FROM agents WHERE user_id = ? AND is_active = 1", (user_id,))
                    else:
                        cursor.execute("SELECT COUNT(*) FROM agents WHERE is_active = 1")
                    
                    return cursor.fetchone()[0]
                    
            except sqlite3.Error as e:
                logger.error(f"Failed to get agent count: {e}")
                return 0
    
    def clear_cache(self):
        """Clear the in-memory agent cache."""
        with self._lock:
            self._cache.clear()
            logger.info("Agent cache cleared")
    
    def __len__(self) -> int:
        """Return the number of cached agents."""
        return len(self._cache)
    
    def __contains__(self, agent_id: str) -> bool:
        """Check if an agent ID exists in the pool."""
        return agent_id in self._cache or self.get_agent(agent_id) is not None
