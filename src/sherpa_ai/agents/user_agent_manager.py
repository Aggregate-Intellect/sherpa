"""User-specific agent management module for Sherpa AI.

This module provides user-specific agent management capabilities, including
personalized agent creation, user preferences, and multi-user support.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from loguru import logger
from pydantic import BaseModel, Field

from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.agents.persistent_agent_pool import PersistentAgentPool, AgentMetadata
from sherpa_ai.agents.agent_serializer import AgentSerializationManager, SerializationContext


class UserPreferences(BaseModel):
    """User preferences for agent management.
    
    Attributes:
        user_id (str): Unique user identifier.
        default_agent_type (str): Default agent type for new agents.
        max_agents (int): Maximum number of agents per user.
        auto_save (bool): Whether to automatically save agent state.
        preferred_llm (str): Preferred LLM model.
        notification_settings (Dict[str, Any]): Notification preferences.
        created_at (datetime): When preferences were created.
        updated_at (datetime): When preferences were last updated.
    """
    
    user_id: str = Field(..., description="Unique user identifier")
    default_agent_type: str = Field(default="QAAgent", description="Default agent type for new agents")
    max_agents: int = Field(default=10, description="Maximum number of agents per user")
    auto_save: bool = Field(default=True, description="Whether to automatically save agent state")
    preferred_llm: str = Field(default="gpt-3.5-turbo", description="Preferred LLM model")
    notification_settings: Dict[str, Any] = Field(default_factory=dict, description="Notification preferences")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserAgentSession(BaseModel):
    """User agent session information.
    
    Attributes:
        session_id (str): Unique session identifier.
        user_id (str): User who owns this session.
        agent_id (str): Agent being used in this session.
        started_at (datetime): When the session started.
        last_activity (datetime): Last activity timestamp.
        is_active (bool): Whether the session is currently active.
        session_data (Dict[str, Any]): Additional session data.
    """
    
    session_id: str = Field(..., description="Unique session identifier")
    user_id: str = Field(..., description="User who owns this session")
    agent_id: str = Field(..., description="Agent being used in this session")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    session_data: Dict[str, Any] = Field(default_factory=dict)


class UserAgentManager:
    """Manages user-specific agents and their interactions.
    
    This class provides comprehensive user-specific agent management,
    including personalized agent creation, session management, and
    user preference handling.
    
    Attributes:
        agent_pool (PersistentAgentPool): The persistent agent pool.
        serialization_manager (AgentSerializationManager): Agent serialization manager.
        user_preferences (Dict[str, UserPreferences]): User preferences cache.
        active_sessions (Dict[str, UserAgentSession]): Active user sessions.
    """
    
    def __init__(self, db_path: str = "user_agents.db"):
        """Initialize the user agent manager.
        
        Args:
            db_path (str): Path to the database file.
            
        Example:
            >>> manager = UserAgentManager("my_user_agents.db")
            >>> print(manager.agent_pool.db_path)
            my_user_agents.db
        """
        self.agent_pool = PersistentAgentPool(db_path)
        self.serialization_manager = AgentSerializationManager()
        self.user_preferences: Dict[str, UserPreferences] = {}
        self.active_sessions: Dict[str, UserAgentSession] = {}
        
        # Initialize user preferences table
        self._init_user_preferences_table()
    
    def _init_user_preferences_table(self):
        """Initialize the user preferences table in the database."""
        try:
            import sqlite3
            with sqlite3.connect(self.agent_pool.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_preferences (
                        user_id TEXT PRIMARY KEY,
                        default_agent_type TEXT NOT NULL DEFAULT 'QAAgent',
                        max_agents INTEGER NOT NULL DEFAULT 10,
                        auto_save BOOLEAN NOT NULL DEFAULT 1,
                        preferred_llm TEXT NOT NULL DEFAULT 'gpt-3.5-turbo',
                        notification_settings TEXT,  -- JSON
                        created_at TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP NOT NULL
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize user preferences table: {e}")
    
    def create_user(self, user_id: str, preferences: Optional[UserPreferences] = None, 
                   **kwargs) -> UserPreferences:
        """Create a new user with default or custom preferences.
        
        Args:
            user_id (str): Unique user identifier.
            preferences (Optional[UserPreferences]): Custom user preferences.
            **kwargs: Additional preferences to override defaults.
            
        Returns:
            UserPreferences: The created user preferences.
            
        Example:
            >>> manager = UserAgentManager()
            >>> prefs = manager.create_user("user123", max_agents=5)
            >>> print(prefs.max_agents)
            5
        """
        if preferences is None:
            # Create preferences with any additional kwargs
            preferences = UserPreferences(user_id=user_id, **kwargs)
        
        # Save to database
        self._save_user_preferences(preferences)
        
        # Cache preferences
        self.user_preferences[user_id] = preferences
        
        logger.info(f"Created user: {user_id}")
        return preferences
    
    def get_user_preferences(self, user_id: str) -> Optional[UserPreferences]:
        """Get user preferences.
        
        Args:
            user_id (str): User identifier.
            
        Returns:
            Optional[UserPreferences]: User preferences or None if not found.
            
        Example:
            >>> manager = UserAgentManager()
            >>> prefs = manager.get_user_preferences("user123")
            >>> print(prefs.max_agents if prefs else "User not found")
            10
        """
        # Check cache first
        if user_id in self.user_preferences:
            return self.user_preferences[user_id]
        
        # Load from database
        try:
            import sqlite3
            with sqlite3.connect(self.agent_pool.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT default_agent_type, max_agents, auto_save, preferred_llm,
                           notification_settings, created_at, updated_at
                    FROM user_preferences WHERE user_id = ?
                """, (user_id,))
                
                row = cursor.fetchone()
                if row:
                    default_agent_type, max_agents, auto_save, preferred_llm, notification_settings, created_at, updated_at = row
                    
                    prefs = UserPreferences(
                        user_id=user_id,
                        default_agent_type=default_agent_type,
                        max_agents=max_agents,
                        auto_save=bool(auto_save),
                        preferred_llm=preferred_llm,
                        notification_settings=json.loads(notification_settings) if notification_settings else {},
                        created_at=datetime.fromisoformat(created_at),
                        updated_at=datetime.fromisoformat(updated_at)
                    )
                    
                    # Cache preferences
                    self.user_preferences[user_id] = prefs
                    return prefs
                    
        except Exception as e:
            logger.error(f"Failed to get user preferences for {user_id}: {e}")
        
        return None
    
    def update_user_preferences(self, user_id: str, **kwargs) -> bool:
        """Update user preferences.
        
        Args:
            user_id (str): User identifier.
            **kwargs: Preference fields to update.
            
        Returns:
            bool: True if successful, False otherwise.
            
        Example:
            >>> manager = UserAgentManager()
            >>> success = manager.update_user_preferences("user123", max_agents=20)
            >>> print("Updated" if success else "Failed")
            Updated
        """
        try:
            prefs = self.get_user_preferences(user_id)
            if not prefs:
                return False
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(prefs, key):
                    setattr(prefs, key, value)
            
            prefs.updated_at = datetime.utcnow()
            
            # Save to database
            self._save_user_preferences(prefs)
            
            # Update cache
            self.user_preferences[user_id] = prefs
            
            logger.info(f"Updated preferences for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update user preferences for {user_id}: {e}")
            return False
    
    def _save_user_preferences(self, preferences: UserPreferences):
        """Save user preferences to database.
        
        Args:
            preferences (UserPreferences): Preferences to save.
        """
        try:
            import sqlite3
            with sqlite3.connect(self.agent_pool.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO user_preferences (
                        user_id, default_agent_type, max_agents, auto_save,
                        preferred_llm, notification_settings, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    preferences.user_id,
                    preferences.default_agent_type,
                    preferences.max_agents,
                    preferences.auto_save,
                    preferences.preferred_llm,
                    json.dumps(preferences.notification_settings),
                    preferences.created_at.isoformat(),
                    preferences.updated_at.isoformat()
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save user preferences: {e}")
            raise
    
    def create_agent_for_user(self, user_id: str, agent_name: str, 
                             agent_type: Optional[str] = None, **kwargs) -> Optional[str]:
        """Create a new agent for a specific user.
        
        Args:
            user_id (str): User identifier.
            agent_name (str): Name for the new agent.
            agent_type (Optional[str]): Type of agent to create.
            **kwargs: Additional agent configuration.
            
        Returns:
            Optional[str]: Agent ID if successful, None otherwise.
            
        Example:
            >>> manager = UserAgentManager()
            >>> agent_id = manager.create_agent_for_user("user123", "My Assistant", "QAAgent")
            >>> print(agent_id if agent_id else "Failed")
            My Assistant_140123456789
        """
        try:
            # Get user preferences
            prefs = self.get_user_preferences(user_id)
            if not prefs:
                # Create user with default preferences
                prefs = self.create_user(user_id)
            
            # Check agent limit
            current_count = self.agent_pool.get_agent_count(user_id)
            if current_count >= prefs.max_agents:
                logger.warning(f"User {user_id} has reached maximum agent limit ({prefs.max_agents})")
                return None
            
            # Determine agent type
            if agent_type is None:
                agent_type = prefs.default_agent_type
            
            # Create agent instance
            agent = self._create_agent_instance(agent_type, agent_name, prefs, **kwargs)
            if not agent:
                return None
            
            # Save agent
            agent_id = self.agent_pool.save_agent(agent, user_id=user_id)
            
            logger.info(f"Created agent '{agent_name}' for user '{user_id}'")
            return agent_id
            
        except Exception as e:
            logger.error(f"Failed to create agent for user {user_id}: {e}")
            return None
    
    def _create_agent_instance(self, agent_type: str, agent_name: str, 
                              preferences: UserPreferences, **kwargs) -> Optional[BaseAgent]:
        """Create an agent instance of the specified type.
        
        Args:
            agent_type (str): Type of agent to create.
            agent_name (str): Name for the agent.
            preferences (UserPreferences): User preferences.
            **kwargs: Additional configuration.
            
        Returns:
            Optional[BaseAgent]: Created agent instance or None if failed.
        """
        try:
            # Import agent classes dynamically
            if agent_type == "QAAgent":
                from sherpa_ai.agents.qa_agent import QAAgent
                return QAAgent(name=agent_name, **kwargs)
            elif agent_type == "MLEngineer":
                from sherpa_ai.agents.ml_engineer import MLEngineer
                return MLEngineer(name=agent_name, **kwargs)
            elif agent_type == "Critic":
                from sherpa_ai.agents.critic import Critic
                return Critic(name=agent_name, **kwargs)
            elif agent_type == "UserAgent":
                from sherpa_ai.agents.user import UserAgent
                return UserAgent(name=agent_name, **kwargs)
            else:
                logger.error(f"Unknown agent type: {agent_type}")
                return None
                
        except ImportError as e:
            logger.error(f"Failed to import agent type {agent_type}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to create agent instance: {e}")
            return None
    
    def get_user_agents(self, user_id: str, active_only: bool = True) -> List[AgentMetadata]:
        """Get all agents for a specific user.
        
        Args:
            user_id (str): User identifier.
            active_only (bool): Only return active agents.
            
        Returns:
            List[AgentMetadata]: List of agent metadata.
            
        Example:
            >>> manager = UserAgentManager()
            >>> agents = manager.get_user_agents("user123")
            >>> for agent in agents:
            ...     print(f"{agent.agent_name} ({agent.agent_type})")
            My Assistant (QAAgent)
        """
        return self.agent_pool.list_agents(user_id=user_id, active_only=active_only)
    
    def get_agent_for_user(self, user_id: str, agent_name: str) -> Optional[BaseAgent]:
        """Get a specific agent for a user.
        
        Args:
            user_id (str): User identifier.
            agent_name (str): Agent name.
            
        Returns:
            Optional[BaseAgent]: The agent if found, None otherwise.
            
        Example:
            >>> manager = UserAgentManager()
            >>> agent = manager.get_agent_for_user("user123", "My Assistant")
            >>> print(agent.name if agent else "Not found")
            My Assistant
        """
        return self.agent_pool.get_agent_by_name(agent_name, user_id)
    
    def start_user_session(self, user_id: str, agent_name: str) -> Optional[str]:
        """Start a new user session with an agent.
        
        Args:
            user_id (str): User identifier.
            agent_name (str): Agent name to use.
            
        Returns:
            Optional[str]: Session ID if successful, None otherwise.
            
        Example:
            >>> manager = UserAgentManager()
            >>> session_id = manager.start_user_session("user123", "My Assistant")
            >>> print(session_id if session_id else "Failed")
            session_140123456789
        """
        try:
            # Get agent
            agent = self.get_agent_for_user(user_id, agent_name)
            if not agent:
                logger.error(f"Agent '{agent_name}' not found for user '{user_id}'")
                return None
            
            # Create session
            session_id = f"session_{int(datetime.utcnow().timestamp())}"
            session = UserAgentSession(
                session_id=session_id,
                user_id=user_id,
                agent_id=agent.name,
                session_data={"agent_type": agent.__class__.__name__}
            )
            
            # Store session
            self.active_sessions[session_id] = session
            
            logger.info(f"Started session {session_id} for user {user_id} with agent {agent_name}")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to start session for user {user_id}: {e}")
            return None
    
    def end_user_session(self, session_id: str) -> bool:
        """End a user session.
        
        Args:
            session_id (str): Session identifier.
            
        Returns:
            bool: True if successful, False otherwise.
            
        Example:
            >>> manager = UserAgentManager()
            >>> success = manager.end_user_session("session_140123456789")
            >>> print("Ended" if success else "Failed")
            Ended
        """
        try:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session.is_active = False
                session.last_activity = datetime.utcnow()
                
                # Remove from active sessions
                del self.active_sessions[session_id]
                
                logger.info(f"Ended session {session_id}")
                return True
            else:
                logger.warning(f"Session {session_id} not found")
                return False
                
        except Exception as e:
            logger.error(f"Failed to end session {session_id}: {e}")
            return False
    
    def get_user_session(self, session_id: str) -> Optional[UserAgentSession]:
        """Get user session information.
        
        Args:
            session_id (str): Session identifier.
            
        Returns:
            Optional[UserAgentSession]: Session information or None if not found.
            
        Example:
            >>> manager = UserAgentManager()
            >>> session = manager.get_user_session("session_140123456789")
            >>> print(session.user_id if session else "Not found")
            user123
        """
        return self.active_sessions.get(session_id)
    
    def get_user_active_sessions(self, user_id: str) -> List[UserAgentSession]:
        """Get all active sessions for a user.
        
        Args:
            user_id (str): User identifier.
            
        Returns:
            List[UserAgentSession]: List of active sessions.
            
        Example:
            >>> manager = UserAgentManager()
            >>> sessions = manager.get_user_active_sessions("user123")
            >>> print(f"User has {len(sessions)} active sessions")
            User has 2 active sessions
        """
        return [session for session in self.active_sessions.values() 
                if session.user_id == user_id and session.is_active]
    
    def auto_save_agent_state(self, user_id: str, agent: BaseAgent) -> bool:
        """Automatically save agent state if user has auto-save enabled.
        
        Args:
            user_id (str): User identifier.
            agent (BaseAgent): Agent to save.
            
        Returns:
            bool: True if saved or auto-save disabled, False if failed.
            
        Example:
            >>> manager = UserAgentManager()
            >>> success = manager.auto_save_agent_state("user123", agent)
            >>> print("Saved" if success else "Failed")
            Saved
        """
        try:
            prefs = self.get_user_preferences(user_id)
            if not prefs or not prefs.auto_save:
                return True  # Auto-save disabled, consider it successful
            
            # Update agent in pool
            agent_id = f"{agent.name}_{id(agent)}"
            return self.agent_pool.update_agent(agent_id, agent)
            
        except Exception as e:
            logger.error(f"Failed to auto-save agent state for user {user_id}: {e}")
            return False
    
    def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get statistics for a user.
        
        Args:
            user_id (str): User identifier.
            
        Returns:
            Dict[str, Any]: User statistics.
            
        Example:
            >>> manager = UserAgentManager()
            >>> stats = manager.get_user_statistics("user123")
            >>> print(f"User has {stats['total_agents']} agents")
            User has 5 agents
        """
        try:
            agents = self.get_user_agents(user_id)
            active_sessions = self.get_user_active_sessions(user_id)
            
            # Count agents by type
            agent_types = {}
            for agent in agents:
                agent_type = agent.agent_type
                agent_types[agent_type] = agent_types.get(agent_type, 0) + 1
            
            return {
                "user_id": user_id,
                "total_agents": len(agents),
                "active_agents": len([a for a in agents if a.is_active]),
                "agent_types": agent_types,
                "active_sessions": len(active_sessions),
                "max_agents": self.get_user_preferences(user_id).max_agents if self.get_user_preferences(user_id) else 10,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get user statistics for {user_id}: {e}")
            return {"error": str(e)}
    
    def cleanup_inactive_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up inactive sessions older than specified hours.
        
        Args:
            max_age_hours (int): Maximum age of sessions in hours.
            
        Returns:
            int: Number of sessions cleaned up.
            
        Example:
            >>> manager = UserAgentManager()
            >>> cleaned = manager.cleanup_inactive_sessions(12)
            >>> print(f"Cleaned up {cleaned} sessions")
            Cleaned up 3 sessions
        """
        try:
            from datetime import timedelta
            
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            sessions_to_remove = []
            
            for session_id, session in self.active_sessions.items():
                if session.last_activity < cutoff_time:
                    sessions_to_remove.append(session_id)
            
            # Remove old sessions
            for session_id in sessions_to_remove:
                del self.active_sessions[session_id]
            
            logger.info(f"Cleaned up {len(sessions_to_remove)} inactive sessions")
            return len(sessions_to_remove)
            
        except Exception as e:
            logger.error(f"Failed to cleanup inactive sessions: {e}")
            return 0
