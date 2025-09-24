"""Persistent Agent Pool module for Sherpa AI.

This module provides a comprehensive agent persistence and retrieval system that supports
user-specific agent management, state serialization, and both SQLite database and JSON file storage.
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
from sherpa_ai.agents.agent_pool import AgentPool
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


class PersistentAgentPool(AgentPool):
    """Enhanced agent pool with persistence and user-specific management.
    
    This class extends the base AgentPool with persistent storage capabilities.
    It provides a comprehensive agent management system that supports:
    - User-specific agent storage and retrieval
    - Agent state persistence across sessions
    - Pydantic validation for data integrity
    - Multiple storage backends (SQLite database and JSON file)
    - Thread-safe operations
    - Agent metadata and tagging
    
    The agents are persisted to either an SQLite database or JSON file based on the storage_type parameter.
    
    Attributes:
        storage_path (str): Path to the storage file (database or JSON).
        storage_type (str): Type of storage backend ('sqlite' or 'json').
        _lock (threading.RLock): Thread safety lock.
    """
    
    def __init__(self, storage_path: str = "agent_pool.db", storage_type: str = "sqlite"):
        """Initialize the persistent agent pool.
        
        Args:
            storage_path (str): Path to the storage file (database or JSON).
            storage_type (str): Type of storage backend ('sqlite' or 'json').
            
        Example:
            >>> # SQLite database storage
            >>> pool = PersistentAgentPool("my_agents.db", "sqlite")
            >>> print(pool.storage_path)
            my_agents.db
            
            >>> # JSON file storage
            >>> pool = PersistentAgentPool("my_agents.json", "json")
            >>> print(pool.storage_path)
            my_agents.json
        """
        # Initialize base AgentPool
        super().__init__()
        
        self.storage_path = storage_path
        self.storage_type = storage_type
        self._lock = threading.RLock()
        
        # Initialize storage backend
        if storage_type == "sqlite":
            self._init_database()
            self._load_agents_from_db()
        elif storage_type == "json":
            self._init_json_storage()
            self._load_agents_from_json()
        else:
            raise ValueError(f"Unsupported storage type: {storage_type}. Use 'sqlite' or 'json'.")
    
    def _init_database(self):
        """Initialize the SQLite database with required tables."""
        with sqlite3.connect(self.storage_path) as conn:
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
    
    def _init_json_storage(self):
        """Initialize JSON file storage."""
        # Create directory if it doesn't exist
        Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Create empty JSON file if it doesn't exist
        if not Path(self.storage_path).exists():
            with open(self.storage_path, 'w') as f:
                json.dump({"agents": []}, f, indent=2)
    
    def _load_agents_from_json(self):
        """Load all active agents from JSON file into cache."""
        with self._lock:
            try:
                if not Path(self.storage_path).exists():
                    return
                
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                
                for agent_data in data.get("agents", []):
                    try:
                        # Skip loading agents from JSON file
                        # Agents are stored but cannot be restored to working state
                        agent_id = agent_data.get("metadata", {}).get("agent_id", "unknown")
                        logger.info(f"Skipping agent {agent_id} - cannot restore from storage")
                                
                    except (json.JSONDecodeError, ValidationError) as e:
                        logger.warning(f"Failed to load agent from JSON: {e}")
                            
            except Exception as e:
                logger.error(f"JSON file error while loading agents: {e}")
    
    def _load_agents_from_db(self):
        """Load all active agents from database into cache."""
        with self._lock:
            try:
                with sqlite3.connect(self.storage_path) as conn:
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
                            # Skip loading agents from database
                            # Agents are stored but cannot be restored to working state
                            logger.info(f"Skipping agent {agent_id} - cannot restore from storage")
                                
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
        
        # Use Pydantic's built-in serialization for the entire agent
        # This is much simpler and leverages BaseAgent's BaseModel inheritance
        # Exclude non-serializable fields and use mode='json' for the rest
        agent_config = agent.model_dump(mode='json', exclude={'prompt_template', 'llm', 'policy', 'actions', 'validations', 'stop_checker'})
        
        # Extract specific state components for easier access
        belief_state = agent_config.get('belief', {}) or {}
        shared_memory_state = agent_config.get('shared_memory', {}) or {}
        
        # Create execution state from agent attributes
        execution_state = {
            'num_runs': agent_config.get('num_runs', 1),
            'validation_steps': agent_config.get('validation_steps', 1),
            'global_regen_max': agent_config.get('global_regen_max', 12)
        }
        
        state = AgentState(
            agent_config=agent_config,
            belief_state=belief_state,
            shared_memory_state=shared_memory_state,
            execution_state=execution_state
        )
        
        return StoredAgent(metadata=metadata, state=state)
    
    def _save_agent_to_db(self, stored_agent: StoredAgent, user_id: str, agent: BaseAgent, overwrite: bool):
        """Save agent to SQLite database."""
        with sqlite3.connect(self.storage_path) as conn:
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
                stored_agent.metadata.agent_id,
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
    
    def _save_agent_to_json(self, stored_agent: StoredAgent, user_id: str, agent: BaseAgent, overwrite: bool):
        """Save agent to JSON file."""
        with self._lock:
            # Load existing data
            if Path(self.storage_path).exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
            else:
                data = {"agents": []}
            
            # Remove existing agent if overwriting
            if overwrite:
                data["agents"] = [a for a in data["agents"] 
                                if not (a.get("metadata", {}).get("user_id") == user_id and 
                                       a.get("metadata", {}).get("agent_name") == agent.name)]
            
            # Add new agent
            agent_data = {
                "metadata": stored_agent.metadata.model_dump(),
                "state": stored_agent.state.model_dump()
            }
            data["agents"].append(agent_data)
            
            # Save to file
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
    
    def _get_agent_from_db(self, agent_id: str) -> Optional[BaseAgent]:
        """Get agent from SQLite database."""
        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT agent_config, belief_state, shared_memory_state, execution_state
                    FROM agents 
                    WHERE agent_id = ? AND is_active = 1
                """, (agent_id,))
                
                row = cursor.fetchone()
                if row:
                    # Agent exists in database but cannot be restored to working state
                    logger.info(f"Agent {agent_id} exists in database but cannot restore from storage")
                    return None
                        
        except (sqlite3.Error, json.JSONDecodeError) as e:
            logger.error(f"Failed to load agent {agent_id}: {e}")
        
        return None
    
    def _get_agent_from_json(self, agent_id: str) -> Optional[BaseAgent]:
        """Get agent from JSON file."""
        try:
            if not Path(self.storage_path).exists():
                return None
            
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            for agent_data in data.get("agents", []):
                if agent_data.get("metadata", {}).get("agent_id") == agent_id:
                    # Agent exists in JSON but cannot be restored to working state
                    logger.info(f"Agent {agent_id} exists in JSON but cannot restore from storage")
                    return None
                        
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Failed to load agent {agent_id} from JSON: {e}")
        
        return None
    
    def _get_agent_by_name_from_db(self, agent_name: str, user_id: str) -> Optional[BaseAgent]:
        """Get agent by name from SQLite database."""
        try:
            with sqlite3.connect(self.storage_path) as conn:
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
    
    def _get_agent_by_name_from_json(self, agent_name: str, user_id: str) -> Optional[BaseAgent]:
        """Get agent by name from JSON file."""
        try:
            if not Path(self.storage_path).exists():
                return None
            
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            for agent_data in data.get("agents", []):
                metadata = agent_data.get("metadata", {})
                if (metadata.get("agent_name") == agent_name and 
                    metadata.get("user_id") == user_id and 
                    metadata.get("is_active", True)):
                    agent_id = metadata.get("agent_id")
                    return self.get_agent(agent_id)
                    
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Failed to find agent '{agent_name}' for user '{user_id}' in JSON: {e}")
        
        return None
    
    def _list_agents_from_db(self, user_id: str, agent_type: str, tags: List[str], active_only: bool) -> List[AgentMetadata]:
        """List agents from SQLite database."""
        try:
            with sqlite3.connect(self.storage_path) as conn:
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
            logger.error(f"Failed to list agents from database: {e}")
            return []
    
    def _list_agents_from_json(self, user_id: str, agent_type: str, tags: List[str], active_only: bool) -> List[AgentMetadata]:
        """List agents from JSON file."""
        try:
            if not Path(self.storage_path).exists():
                return []
            
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            agents = []
            for agent_data in data.get("agents", []):
                metadata_dict = agent_data.get("metadata", {})
                
                # Apply filters
                if user_id and metadata_dict.get("user_id") != user_id:
                    continue
                if agent_type and metadata_dict.get("agent_type") != agent_type:
                    continue
                if active_only and not metadata_dict.get("is_active", True):
                    continue
                
                # Check tag filter
                agent_tags = metadata_dict.get("tags", [])
                if tags and not any(tag in agent_tags for tag in tags):
                    continue
                
                metadata = AgentMetadata(
                    agent_id=metadata_dict.get("agent_id", ""),
                    user_id=metadata_dict.get("user_id", ""),
                    agent_name=metadata_dict.get("agent_name", ""),
                    agent_type=metadata_dict.get("agent_type", ""),
                    created_at=datetime.fromisoformat(metadata_dict.get("created_at", datetime.utcnow().isoformat())),
                    updated_at=datetime.fromisoformat(metadata_dict.get("updated_at", datetime.utcnow().isoformat())),
                    is_active=metadata_dict.get("is_active", True),
                    tags=agent_tags,
                    description=metadata_dict.get("description", "")
                )
                agents.append(metadata)
            
            return agents
            
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Failed to list agents from JSON: {e}")
            return []
    
    def _delete_agent_from_db(self, agent_id: str, soft_delete: bool) -> bool:
        """Delete agent from SQLite database."""
        try:
            with sqlite3.connect(self.storage_path) as conn:
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
                if agent_id in self.agents:
                    del self.agents[agent_id]
                
                logger.info(f"Deleted agent {agent_id} from database (soft_delete={soft_delete})")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Failed to delete agent {agent_id} from database: {e}")
            return False
    
    def _delete_agent_from_json(self, agent_id: str, soft_delete: bool) -> bool:
        """Delete agent from JSON file."""
        try:
            if not Path(self.storage_path).exists():
                return False
            
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            # Find and update/remove agent
            for i, agent_data in enumerate(data.get("agents", [])):
                if agent_data.get("metadata", {}).get("agent_id") == agent_id:
                    if soft_delete:
                        # Mark as inactive
                        data["agents"][i]["metadata"]["is_active"] = False
                        data["agents"][i]["metadata"]["updated_at"] = datetime.utcnow().isoformat()
                    else:
                        # Remove completely
                        data["agents"].pop(i)
                    break
            else:
                return False  # Agent not found
            
            # Save updated data
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Remove from cache
            if agent_id in self.agents:
                del self.agents[agent_id]
            
            logger.info(f"Deleted agent {agent_id} from JSON (soft_delete={soft_delete})")
            return True
            
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Failed to delete agent {agent_id} from JSON: {e}")
            return False
    
    def _update_agent_in_db(self, agent_id: str, agent: BaseAgent) -> bool:
        """Update agent in SQLite database."""
        try:
            # Serialize updated agent
            stored_agent = self._serialize_agent(agent)
            
            with sqlite3.connect(self.storage_path) as conn:
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
            self.agents[agent_id] = agent
            
            logger.info(f"Updated agent {agent_id} in database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update agent {agent_id} in database: {e}")
            return False
    
    def _update_agent_in_json(self, agent_id: str, agent: BaseAgent) -> bool:
        """Update agent in JSON file."""
        try:
            if not Path(self.storage_path).exists():
                return False
            
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            # Find and update agent
            for i, agent_data in enumerate(data.get("agents", [])):
                if agent_data.get("metadata", {}).get("agent_id") == agent_id:
                    # Serialize updated agent
                    stored_agent = self._serialize_agent(agent)
                    
                    # Update agent data
                    data["agents"][i] = {
                        "metadata": stored_agent.metadata.model_dump(),
                        "state": stored_agent.state.model_dump()
                    }
                    break
            else:
                return False  # Agent not found
            
            # Save updated data
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Update cache
            self.agents[agent_id] = agent
            
            logger.info(f"Updated agent {agent_id} in JSON")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update agent {agent_id} in JSON: {e}")
            return False
    
    def _get_agent_count_from_db(self, user_id: str) -> int:
        """Get agent count from SQLite database."""
        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.cursor()
                
                if user_id:
                    cursor.execute("SELECT COUNT(*) FROM agents WHERE user_id = ? AND is_active = 1", (user_id,))
                else:
                    cursor.execute("SELECT COUNT(*) FROM agents WHERE is_active = 1")
                
                return cursor.fetchone()[0]
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get agent count from database: {e}")
            return 0
    
    def _get_agent_count_from_json(self, user_id: str) -> int:
        """Get agent count from JSON file."""
        try:
            if not Path(self.storage_path).exists():
                return 0
            
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            count = 0
            for agent_data in data.get("agents", []):
                metadata = agent_data.get("metadata", {})
                if metadata.get("is_active", True):
                    if user_id is None or metadata.get("user_id") == user_id:
                        count += 1
            
            return count
            
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Failed to get agent count from JSON: {e}")
            return 0
    
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
                
                # Save to storage backend
                if self.storage_type == "sqlite":
                    self._save_agent_to_db(stored_agent, user_id, agent, overwrite)
                elif self.storage_type == "json":
                    self._save_agent_to_json(stored_agent, user_id, agent, overwrite)
                
                # Add to cache
                self.agents[agent_id] = agent
                
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
            if agent_id in self.agents:
                return self.agents[agent_id]
            
            # Load from storage backend
            if self.storage_type == "sqlite":
                return self._get_agent_from_db(agent_id)
            elif self.storage_type == "json":
                return self._get_agent_from_json(agent_id)
            
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
            if self.storage_type == "sqlite":
                return self._get_agent_by_name_from_db(agent_name, user_id)
            elif self.storage_type == "json":
                return self._get_agent_by_name_from_json(agent_name, user_id)
            
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
            if self.storage_type == "sqlite":
                return self._list_agents_from_db(user_id, agent_type, tags, active_only)
            elif self.storage_type == "json":
                return self._list_agents_from_json(user_id, agent_type, tags, active_only)
            
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
            if self.storage_type == "sqlite":
                return self._delete_agent_from_db(agent_id, soft_delete)
            elif self.storage_type == "json":
                return self._delete_agent_from_json(agent_id, soft_delete)
            
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
            if self.storage_type == "sqlite":
                return self._update_agent_in_db(agent_id, agent)
            elif self.storage_type == "json":
                return self._update_agent_in_json(agent_id, agent)
            
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
            if self.storage_type == "sqlite":
                return self._get_agent_count_from_db(user_id)
            elif self.storage_type == "json":
                return self._get_agent_count_from_json(user_id)
            
            return 0
    
    def clear_cache(self):
        """Clear the in-memory agent cache."""
        with self._lock:
            self.agents.clear()
            logger.info("Agent cache cleared")
    
    def __len__(self) -> int:
        """Return the number of cached agents."""
        return len(self.agents)
    
    def __contains__(self, agent_id: str) -> bool:
        """Check if an agent ID exists in the pool."""
        return agent_id in self.agents or self.get_agent(agent_id) is not None
