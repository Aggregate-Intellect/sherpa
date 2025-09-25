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
from functools import wraps

from loguru import logger
from pydantic import BaseModel, Field, ValidationError

from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.agents.agent_pool import AgentPool
from sherpa_ai.memory.belief import Belief


def handle_storage_errors(default_return=None):
    """Decorator to handle common storage operation errors.
    
    Args:
        default_return: Value to return on error (None, False, [], etc.)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except (sqlite3.Error, json.JSONDecodeError, ValidationError) as e:
                logger.error(f"Storage operation failed in {func.__name__}: {e}")
                return default_return
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {e}")
                return default_return
        return wrapper
    return decorator


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
                
                # Check if file is empty
                if Path(self.storage_path).stat().st_size == 0:
                    return
                
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                
                for agent_data in data.get("agents", []):
                    try:
                        # Deserialize agent from JSON data
                        stored_agent = StoredAgent(
                            metadata=AgentMetadata(**agent_data.get("metadata", {})),
                            state=AgentState(**agent_data.get("state", {}))
                        )
                        
                        # Restore agent to working state
                        agent = self._deserialize_agent(stored_agent)
                        if agent:
                            agent_id = stored_agent.metadata.agent_id
                            self.agents[agent_id] = agent
                            logger.info(f"Restored agent {agent_id} from JSON storage")
                        else:
                            logger.warning(f"Failed to restore agent {stored_agent.metadata.agent_name} from JSON")
                                
                    except (json.JSONDecodeError, ValidationError) as e:
                        logger.warning(f"Failed to load agent from JSON: {e}")
                            
            except Exception as e:
                logger.error(f"JSON file error while loading agents: {e}")
    
    @handle_storage_errors()
    def _load_agents_from_db(self):
        """Load all active agents from database into cache."""
        with self._lock:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.cursor()
                # Single query to get all data
                cursor.execute("""
                    SELECT agent_id, user_id, agent_name, agent_type, created_at, updated_at,
                           is_active, tags, description, agent_config, belief_state, 
                           shared_memory_state, execution_state
                    FROM agents 
                    WHERE is_active = 1
                """)
                
                for row in cursor.fetchall():
                    (agent_id, user_id, agent_name, agent_type, created_at, updated_at,
                     is_active, tags, description, config_json, belief_json, memory_json, exec_json) = row
                    
                    try:
                        # Parse JSON data
                        agent_config = json.loads(config_json) if config_json else {}
                        belief_state = json.loads(belief_json) if belief_json else {}
                        shared_memory_state = json.loads(memory_json) if memory_json else {}
                        execution_state = json.loads(exec_json) if exec_json else {}
                        
                        # Create metadata
                        metadata = AgentMetadata(
                            agent_id=agent_id,
                            user_id=user_id,
                            agent_name=agent_name,
                            agent_type=agent_type,
                            created_at=datetime.fromisoformat(created_at),
                            updated_at=datetime.fromisoformat(updated_at),
                            is_active=bool(is_active),
                            tags=json.loads(tags) if tags else [],
                            description=description or ""
                        )
                        
                        # Create state
                        state = AgentState(
                            agent_config=agent_config,
                            belief_state=belief_state,
                            shared_memory_state=shared_memory_state,
                            execution_state=execution_state
                        )
                        
                        stored_agent = StoredAgent(metadata=metadata, state=state)
                        
                        # Restore agent to working state
                        agent = self._deserialize_agent(stored_agent)
                        if agent:
                            self.agents[agent_id] = agent
                            logger.info(f"Restored agent {agent_id} from database")
                        else:
                            logger.warning(f"Failed to restore agent {agent_name} from database")
                            
                    except (json.JSONDecodeError, ValidationError) as e:
                        logger.warning(f"Failed to load agent {agent_id}: {e}")
    
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
        # Exclude non-serializable fields and use mode='json' for the rest
        agent_config = agent.model_dump(
            mode='json', 
            exclude={'prompt_template', 'llm', 'policy', 'actions', 'validations', 'stop_checker'}
        )
        
        # Preserve timestamp fields to avoid regeneration during deserialization
        self._preserve_timestamps(agent, agent_config)
        
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
    
    def _preserve_timestamps(self, agent: BaseAgent, agent_config: Dict[str, Any]):
        """Preserve timestamp fields in agent configuration.
        
        Args:
            agent (BaseAgent): The agent being serialized.
            agent_config (Dict[str, Any]): The agent configuration dictionary.
        """
        # Preserve last_execution_time
        if hasattr(agent, 'last_execution_time') and agent.last_execution_time:
            agent_config['last_execution_time'] = agent.last_execution_time.isoformat()
        
        # Preserve state history with timestamps
        if hasattr(agent, 'state_history') and agent.state_history:
            agent_config['state_history'] = []
            for entry in agent.state_history:
                if isinstance(entry, dict) and 'timestamp' in entry:
                    # Ensure timestamp is in ISO format
                    entry_copy = entry.copy()
                    if hasattr(entry['timestamp'], 'isoformat'):
                        entry_copy['timestamp'] = entry['timestamp'].isoformat()
                    agent_config['state_history'].append(entry_copy)
                else:
                    agent_config['state_history'].append(entry)
    
    def _deserialize_agent(self, stored_agent: StoredAgent) -> Optional[BaseAgent]:
        """Deserialize a StoredAgent back to a working BaseAgent.
        
        Args:
            stored_agent (StoredAgent): The stored agent data.
            
        Returns:
            Optional[BaseAgent]: The deserialized agent or None if failed.
        """
        try:
            # Get agent class from type
            agent_type = stored_agent.metadata.agent_type
            agent_class = self._get_agent_class(agent_type)
            
            if not agent_class:
                logger.error(f"Unknown agent type: {agent_type}")
            return None
            
            # Create agent instance with basic parameters
            agent = agent_class(
                name=stored_agent.metadata.agent_name,
                description=stored_agent.metadata.description
            )
            
            # Restore agent attributes from stored state
            agent_config = stored_agent.state.agent_config
            
            # Restore basic attributes
            if 'num_runs' in agent_config:
                agent.num_runs = agent_config['num_runs']
            if 'validation_steps' in agent_config:
                agent.validation_steps = agent_config['validation_steps']
            if 'global_regen_max' in agent_config:
                agent.global_regen_max = agent_config['global_regen_max']
            if 'feedback_agent_name' in agent_config:
                agent.feedback_agent_name = agent_config['feedback_agent_name']
            
            # Restore user_id and tags
            agent.user_id = stored_agent.metadata.user_id
            agent.tags = stored_agent.metadata.tags
            
            # Restore timestamp fields to preserve exact timing
            if 'last_execution_time' in agent_config and agent_config['last_execution_time']:
                from datetime import datetime
                try:
                    # Parse ISO format timestamp back to datetime object
                    agent.last_execution_time = datetime.fromisoformat(agent_config['last_execution_time'])
                except (ValueError, TypeError):
                    # If parsing fails, keep the string value
                    agent.last_execution_time = agent_config['last_execution_time']
            
            # Restore execution count to preserve state
            if 'execution_count' in agent_config:
                agent.execution_count = agent_config['execution_count']
            
            # Restore complex data structures
            if 'complex_data' in agent_config:
                agent.complex_data = agent_config['complex_data']
            
            if 'custom_actions' in agent_config:
                agent.custom_actions = agent_config['custom_actions']
            
            if 'configuration' in agent_config:
                agent.configuration = agent_config['configuration']
            
            # Restore state history with preserved timestamps
            if 'state_history' in agent_config and agent_config['state_history']:
                agent.state_history = []
                for entry in agent_config['state_history']:
                    if isinstance(entry, dict) and 'timestamp' in entry:
                        # Parse timestamp back to datetime if it's a string
                        entry_copy = entry.copy()
                        if isinstance(entry['timestamp'], str):
                            try:
                                entry_copy['timestamp'] = datetime.fromisoformat(entry['timestamp'])
                            except (ValueError, TypeError):
                                # Keep as string if parsing fails
                                pass
                        agent.state_history.append(entry_copy)
                    else:
                        agent.state_history.append(entry)
            
            # Restore belief state
            if stored_agent.state.belief_state:
                agent.belief = self._deserialize_belief(stored_agent.state.belief_state)
            
            # Restore shared memory
            if stored_agent.state.shared_memory_state:
                agent.shared_memory = self._deserialize_shared_memory(stored_agent.state.shared_memory_state)
            
            # Note: LLM, Policy, Actions, and other complex objects are not restored
            # as they require specific initialization that may not be available
            # The agent will need to be reconfigured with these components
            
            logger.info(f"Deserialized agent {stored_agent.metadata.agent_name} of type {agent_type}")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to deserialize agent {stored_agent.metadata.agent_name}: {e}")
            return None
    
    def _get_agent_class(self, agent_type: str) -> Optional[type]:
        """Get agent class by type name.
        
        Args:
            agent_type (str): The agent type name.
            
        Returns:
            Optional[type]: The agent class or None if not found.
        """
        # Registry of known agent types
        agent_registry = {
            "QAAgent": "sherpa_ai.agents.qa_agent",
            "ResearchAgent": "sherpa_ai.agents.research_agent", 
            "CriticAgent": "sherpa_ai.agents.critic_agent",
            "BaseAgent": None  # Direct import
        }
        
        try:
            # Check registry first
            if agent_type in agent_registry:
                if agent_type == "BaseAgent":
                    return BaseAgent
                else:
                    module_path = agent_registry[agent_type]
                    module = __import__(module_path, fromlist=[agent_type])
                    return getattr(module, agent_type)
            
            # Try to find in current module's globals
            import sys
            current_module = sys.modules[__name__]
            if hasattr(current_module, agent_type):
                return getattr(current_module, agent_type)
            
            # Try to find in calling module's globals
            import inspect
            frame = inspect.currentframe()
            try:
                for _ in range(3):  # Check up to 3 frames up
                    frame = frame.f_back
                    if frame is None:
                        break
                    caller_globals = frame.f_globals
                    if agent_type in caller_globals:
                        return caller_globals[agent_type]
            finally:
                del frame
            
            # Fallback to BaseAgent for unknown types ending with "Agent"
            if agent_type.endswith("Agent"):
                logger.warning(f"Unknown agent type: {agent_type}, falling back to BaseAgent")
                return BaseAgent
            
            logger.warning(f"Unknown agent type: {agent_type}")
            return None
            
        except ImportError as e:
            logger.error(f"Failed to import agent type {agent_type}: {e}")
            return None
    
    def _deserialize_belief(self, belief_data: Dict[str, Any]) -> Optional[Belief]:
        """Deserialize belief state.
        
        Args:
            belief_data (Dict[str, Any]): Serialized belief data.
            
        Returns:
            Optional[Belief]: Deserialized belief or None if failed.
        """
        try:
            if not belief_data:
                return None
            
            # Create a new Belief instance
            belief = Belief()
            
            # Restore belief content if available
            if 'content' in belief_data:
                belief.content = belief_data['content']
            
            return belief
            
        except Exception as e:
            logger.warning(f"Failed to deserialize belief: {e}")
            return None
    
    def _get_agent_metadata_from_db(self, agent_id: str) -> Optional[AgentMetadata]:
        """Get agent metadata from database in a single query.
        
        Args:
            agent_id (str): The agent ID to get metadata for.
            
        Returns:
            Optional[AgentMetadata]: Agent metadata or None if not found.
        """
        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT user_id, agent_name, agent_type, created_at, updated_at, 
                           is_active, tags, description
                    FROM agents WHERE agent_id = ?
                """, (agent_id,))
                
                row = cursor.fetchone()
                if row:
                    user_id, agent_name, agent_type, created_at, updated_at, is_active, tags, description = row
                    return AgentMetadata(
                        agent_id=agent_id,
                        user_id=user_id,
                        agent_name=agent_name,
                        agent_type=agent_type,
                        created_at=datetime.fromisoformat(created_at),
                        updated_at=datetime.fromisoformat(updated_at),
                        is_active=bool(is_active),
                        tags=json.loads(tags) if tags else [],
                        description=description or ""
                    )
                return None
        except (sqlite3.Error, json.JSONDecodeError) as e:
            logger.error(f"Failed to get metadata for agent {agent_id}: {e}")
            return None

    def _deserialize_shared_memory(self, memory_data: Dict[str, Any]):
        """Deserialize shared memory state.
        
        Args:
            memory_data (Dict[str, Any]): Serialized memory data.
            
        Returns:
            Optional[SharedMemory]: Deserialized memory or None if failed.
        """
        try:
            if not memory_data:
                return None
            
            from sherpa_ai.memory.shared_memory import SharedMemory
            memory = SharedMemory()
            
            # Restore memory content if available
            if 'content' in memory_data:
                memory.content = memory_data['content']
            
            return memory
            
        except Exception as e:
            logger.warning(f"Failed to deserialize shared memory: {e}")
            return None
    
    def _execute_storage_operation(self, operation: str, *args, **kwargs):
        """Execute storage operation based on storage type.
        
        Args:
            operation (str): The operation to perform ('save', 'get', 'list', 'delete', 'update', 'get_agent_by_name', 'get_agent_count').
            *args: Positional arguments for the operation.
            **kwargs: Keyword arguments for the operation.
            
        Returns:
            Any: Result of the operation.
        """
        # Map operations to method names
        operation_mapping = {
            'save': 'save_agent_to',
            'get': 'get_agent_from',
            'list': 'list_agents_from',
            'delete': 'delete_agent_from',
            'update': 'update_agent_in',
            'get_agent_by_name': 'get_agent_by_name_from',
            'get_agent_count': 'get_agent_count_from'
        }
        
        if operation not in operation_mapping:
            raise ValueError(f"Unknown operation: {operation}")
        
        base_method = operation_mapping[operation]
        
        if self.storage_type == "sqlite":
            method_name = f"_{base_method}_db"
        elif self.storage_type == "json":
            method_name = f"_{base_method}_json"
        else:
            raise ValueError(f"Unsupported storage type: {self.storage_type}")
        
        method = getattr(self, method_name, None)
        if method:
            return method(*args, **kwargs)
        else:
            raise AttributeError(f"Operation '{operation}' not supported for storage type '{self.storage_type}'")
    
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
            if Path(self.storage_path).exists() and Path(self.storage_path).stat().st_size > 0:
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
                "metadata": stored_agent.metadata.model_dump(mode='json'),
                "state": stored_agent.state.model_dump(mode='json')
            }
            data["agents"].append(agent_data)
            
            # Save to file
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
    
    @handle_storage_errors(default_return=None)
    def _get_agent_from_db(self, agent_id: str) -> Optional[BaseAgent]:
        """Get agent from SQLite database."""
        with sqlite3.connect(self.storage_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT agent_config, belief_state, shared_memory_state, execution_state
                FROM agents 
                WHERE agent_id = ? AND is_active = 1
            """, (agent_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
                
            config_json, belief_json, memory_json, exec_json = row
            
            # Parse JSON data
            agent_config = json.loads(config_json) if config_json else {}
            belief_state = json.loads(belief_json) if belief_json else {}
            shared_memory_state = json.loads(memory_json) if memory_json else {}
            execution_state = json.loads(exec_json) if exec_json else {}
            
            # Get metadata using helper method
            metadata = self._get_agent_metadata_from_db(agent_id)
            if not metadata:
                return None
                
            state = AgentState(
                agent_config=agent_config,
                belief_state=belief_state,
                shared_memory_state=shared_memory_state,
                execution_state=execution_state
            )
            
            stored_agent = StoredAgent(metadata=metadata, state=state)
            
            # Restore agent to working state
            agent = self._deserialize_agent(stored_agent)
            if agent:
                # Cache the restored agent
                self.agents[agent_id] = agent
                logger.info(f"Restored agent {agent_id} from database")
                return agent
            else:
                logger.warning(f"Failed to restore agent {metadata.agent_name} from database")
                return None
    
    @handle_storage_errors(default_return=None)
    def _get_agent_from_json(self, agent_id: str) -> Optional[BaseAgent]:
        """Get agent from JSON file."""
        try:
            if not Path(self.storage_path).exists():
                return None
            
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            for agent_data in data.get("agents", []):
                if agent_data.get("metadata", {}).get("agent_id") == agent_id:
                    # Deserialize agent from JSON data
                    stored_agent = StoredAgent(
                        metadata=AgentMetadata(**agent_data.get("metadata", {})),
                        state=AgentState(**agent_data.get("state", {}))
                    )
                    
                    # Restore agent to working state
                    agent = self._deserialize_agent(stored_agent)
                    if agent:
                        # Cache the restored agent
                        self.agents[agent_id] = agent
                        logger.info(f"Restored agent {agent_id} from JSON storage")
                        return agent
                    else:
                        logger.warning(f"Failed to restore agent {stored_agent.metadata.agent_name} from JSON")
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
                        "metadata": stored_agent.metadata.model_dump(mode='json'),
                        "state": stored_agent.state.model_dump(mode='json')
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
            return self._execute_storage_operation("get", agent_id)
    
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
            return self._execute_storage_operation("get_agent_by_name", agent_name, user_id)
    
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
            return self._execute_storage_operation("list", user_id, agent_type, tags, active_only)
    
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
            return self._execute_storage_operation("delete", agent_id, soft_delete)
    
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
            return self._execute_storage_operation("update", agent_id, agent)
    
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
            return self._execute_storage_operation("get_agent_count", user_id)
    
    def clear_cache(self):
        """Clear the in-memory agent cache."""
        with self._lock:
            self.agents.clear()
            logger.info("Agent cache cleared")
    
    def reload_from_storage(self):
        """Reload all agents from storage into cache.
        
        This method leverages the base AgentPool's agents dictionary
        and repopulates it from the persistent storage.
        """
        with self._lock:
            # Clear current cache
            self.agents.clear()
            
            # Reload from storage
            if self.storage_type == "sqlite":
                self._load_agents_from_db()
            elif self.storage_type == "json":
                self._load_agents_from_json()
            
            logger.info(f"Reloaded {len(self.agents)} agents from {self.storage_type} storage")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the current cache state.
        
        Returns:
            Dict[str, Any]: Cache statistics including size, storage type, etc.
        """
        with self._lock:
            return {
                "cache_size": len(self.agents),
                "storage_type": self.storage_type,
                "storage_path": self.storage_path,
                "agent_ids": list(self.agents.keys()),
                "agent_types": list(set(agent.__class__.__name__ for agent in self.agents.values()))
            }
    
    def __len__(self) -> int:
        """Return the number of cached agents."""
        return len(self.agents)
    
    def __contains__(self, agent_id: str) -> bool:
        """Check if an agent ID exists in the pool."""
        return agent_id in self.agents or self.get_agent(agent_id) is not None
