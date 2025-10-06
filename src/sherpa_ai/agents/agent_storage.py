"""Agent storage and database management module for Sherpa AI.

This module provides database schema management, migrations, and storage utilities
for the persistent agent pool system.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger
from pydantic import BaseModel, Field


class DatabaseMigration(BaseModel):
    """Database migration definition.
    
    Attributes:
        version (int): Migration version number.
        description (str): Description of what the migration does.
        up_sql (str): SQL to apply the migration.
        down_sql (str): SQL to rollback the migration.
        created_at (datetime): When the migration was created.
    """
    
    version: int = Field(..., description="Migration version number")
    description: str = Field(..., description="Description of what the migration does")
    up_sql: str = Field(..., description="SQL to apply the migration")
    down_sql: str = Field(..., description="SQL to rollback the migration")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AgentStorageManager:
    """Manages agent storage, database schema, and migrations.
    
    This class provides comprehensive database management for agent persistence,
    including schema creation, migrations, and data integrity checks.
    
    Attributes:
        db_path (str): Path to the SQLite database file.
        migrations_table (str): Name of the migrations tracking table.
    """
    
    def __init__(self, db_path: str = "agent_pool.db"):
        """Initialize the storage manager.
        
        Args:
            db_path (str): Path to the SQLite database file.
            
        Example:
            >>> storage = AgentStorageManager("my_agents.db")
            >>> storage.initialize_database()
        """
        self.db_path = db_path
        self.migrations_table = "schema_migrations"
        
        # Define available migrations
        self.migrations = self._get_migrations()
    
    def _get_migrations(self) -> List[DatabaseMigration]:
        """Get the list of available database migrations.
        
        Returns:
            List[DatabaseMigration]: List of migration definitions.
        """
        return [
            DatabaseMigration(
                version=1,
                description="Initial agent storage schema",
                up_sql="""
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
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_user_id ON agents(user_id);
                    CREATE INDEX IF NOT EXISTS idx_agent_name ON agents(agent_name);
                    CREATE INDEX IF NOT EXISTS idx_agent_type ON agents(agent_type);
                    CREATE INDEX IF NOT EXISTS idx_is_active ON agents(is_active);
                    CREATE INDEX IF NOT EXISTS idx_created_at ON agents(created_at);
                    CREATE INDEX IF NOT EXISTS idx_updated_at ON agents(updated_at);
                """,
                down_sql="DROP TABLE IF EXISTS agents;"
            ),
            DatabaseMigration(
                version=2,
                description="Add agent sessions and conversation history",
                up_sql="""
                    CREATE TABLE IF NOT EXISTS agent_sessions (
                        session_id TEXT PRIMARY KEY,
                        agent_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        started_at TIMESTAMP NOT NULL,
                        ended_at TIMESTAMP,
                        is_active BOOLEAN NOT NULL DEFAULT 1,
                        session_data TEXT,  -- JSON
                        FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                    );
                    
                    CREATE TABLE IF NOT EXISTS conversation_history (
                        message_id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        message_type TEXT NOT NULL,  -- 'user', 'agent', 'system'
                        content TEXT NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        metadata TEXT,  -- JSON
                        FOREIGN KEY (session_id) REFERENCES agent_sessions(session_id)
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_session_agent_id ON agent_sessions(agent_id);
                    CREATE INDEX IF NOT EXISTS idx_session_user_id ON agent_sessions(user_id);
                    CREATE INDEX IF NOT EXISTS idx_session_active ON agent_sessions(is_active);
                    CREATE INDEX IF NOT EXISTS idx_conversation_session_id ON conversation_history(session_id);
                    CREATE INDEX IF NOT EXISTS idx_conversation_timestamp ON conversation_history(timestamp);
                """,
                down_sql="""
                    DROP TABLE IF EXISTS conversation_history;
                    DROP TABLE IF EXISTS agent_sessions;
                """
            ),
            DatabaseMigration(
                version=3,
                description="Add agent performance metrics and analytics",
                up_sql="""
                    CREATE TABLE IF NOT EXISTS agent_metrics (
                        metric_id TEXT PRIMARY KEY,
                        agent_id TEXT NOT NULL,
                        metric_type TEXT NOT NULL,  -- 'execution_time', 'token_usage', 'success_rate', etc.
                        metric_value REAL NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        metadata TEXT,  -- JSON
                        FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                    );
                    
                    CREATE TABLE IF NOT EXISTS agent_analytics (
                        analytics_id TEXT PRIMARY KEY,
                        agent_id TEXT NOT NULL,
                        date DATE NOT NULL,
                        total_executions INTEGER DEFAULT 0,
                        successful_executions INTEGER DEFAULT 0,
                        failed_executions INTEGER DEFAULT 0,
                        avg_execution_time REAL DEFAULT 0,
                        total_tokens_used INTEGER DEFAULT 0,
                        user_interactions INTEGER DEFAULT 0,
                        FOREIGN KEY (agent_id) REFERENCES agents(agent_id),
                        UNIQUE(agent_id, date)
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_metrics_agent_id ON agent_metrics(agent_id);
                    CREATE INDEX IF NOT EXISTS idx_metrics_type ON agent_metrics(metric_type);
                    CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON agent_metrics(timestamp);
                    CREATE INDEX IF NOT EXISTS idx_analytics_agent_id ON agent_analytics(agent_id);
                    CREATE INDEX IF NOT EXISTS idx_analytics_date ON agent_analytics(date);
                """,
                down_sql="""
                    DROP TABLE IF EXISTS agent_analytics;
                    DROP TABLE IF EXISTS agent_metrics;
                """
            )
        ]
    
    def initialize_database(self) -> bool:
        """Initialize the database with the latest schema.
        
        Returns:
            bool: True if successful, False otherwise.
            
        Example:
            >>> storage = AgentStorageManager()
            >>> success = storage.initialize_database()
            >>> print("Database initialized" if success else "Failed")
            Database initialized
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Create migrations table
                conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.migrations_table} (
                        version INTEGER PRIMARY KEY,
                        applied_at TIMESTAMP NOT NULL,
                        description TEXT NOT NULL
                    )
                """)
                
                # Apply all pending migrations
                self._apply_migrations(conn)
                
                conn.commit()
                logger.info(f"Database initialized successfully: {self.db_path}")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database: {e}")
            return False
    
    def _apply_migrations(self, conn: sqlite3.Connection):
        """Apply pending database migrations.
        
        Args:
            conn (sqlite3.Connection): Database connection.
        """
        # Get applied migrations
        cursor = conn.cursor()
        cursor.execute(f"SELECT version FROM {self.migrations_table} ORDER BY version")
        applied_versions = {row[0] for row in cursor.fetchall()}
        
        # Apply pending migrations
        for migration in self.migrations:
            if migration.version not in applied_versions:
                logger.info(f"Applying migration {migration.version}: {migration.description}")
                
                try:
                    # Execute migration SQL
                    conn.executescript(migration.up_sql)
                    
                    # Record migration
                    cursor.execute(f"""
                        INSERT INTO {self.migrations_table} (version, applied_at, description)
                        VALUES (?, ?, ?)
                    """, (migration.version, datetime.utcnow().isoformat(), migration.description))
                    
                    logger.info(f"Migration {migration.version} applied successfully")
                    
                except sqlite3.Error as e:
                    logger.error(f"Failed to apply migration {migration.version}: {e}")
                    raise
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get information about the database.
        
        Returns:
            Dict[str, Any]: Database information including tables, indexes, and statistics.
            
        Example:
            >>> storage = AgentStorageManager()
            >>> info = storage.get_database_info()
            >>> print(f"Database has {info['table_count']} tables")
            Database has 4 tables
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get table information
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                # Get index information
                cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
                indexes = [row[0] for row in cursor.fetchall()]
                
                # Get applied migrations
                cursor.execute(f"SELECT version, applied_at, description FROM {self.migrations_table} ORDER BY version")
                migrations = [{"version": row[0], "applied_at": row[1], "description": row[2]} for row in cursor.fetchall()]
                
                # Get database statistics
                stats = {}
                if "agents" in tables:
                    cursor.execute("SELECT COUNT(*) FROM agents WHERE is_active = 1")
                    stats["active_agents"] = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM agents")
                    stats["total_agents"] = cursor.fetchone()[0]
                
                if "agent_sessions" in tables:
                    cursor.execute("SELECT COUNT(*) FROM agent_sessions WHERE is_active = 1")
                    stats["active_sessions"] = cursor.fetchone()[0]
                
                return {
                    "database_path": self.db_path,
                    "table_count": len(tables),
                    "index_count": len(indexes),
                    "tables": tables,
                    "indexes": indexes,
                    "migrations": migrations,
                    "statistics": stats
                }
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get database info: {e}")
            return {"error": str(e)}
    
    def backup_database(self, backup_path: str) -> bool:
        """Create a backup of the database.
        
        Args:
            backup_path (str): Path where to save the backup.
            
        Returns:
            bool: True if successful, False otherwise.
            
        Example:
            >>> storage = AgentStorageManager()
            >>> success = storage.backup_database("backup_agents.db")
            >>> print("Backup created" if success else "Failed")
            Backup created
        """
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backed up to: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            return False
    
    def restore_database(self, backup_path: str) -> bool:
        """Restore database from backup.
        
        Args:
            backup_path (str): Path to the backup file.
            
        Returns:
            bool: True if successful, False otherwise.
            
        Example:
            >>> storage = AgentStorageManager()
            >>> success = storage.restore_database("backup_agents.db")
            >>> print("Database restored" if success else "Failed")
            Database restored
        """
        try:
            import shutil
            shutil.copy2(backup_path, self.db_path)
            logger.info(f"Database restored from: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore database: {e}")
            return False
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> Dict[str, int]:
        """Clean up old data from the database.
        
        Args:
            days_to_keep (int): Number of days of data to keep.
            
        Returns:
            Dict[str, int]: Number of records cleaned up by table.
            
        Example:
            >>> storage = AgentStorageManager()
            >>> cleaned = storage.cleanup_old_data(7)  # Keep 7 days
            >>> print(f"Cleaned {cleaned['conversations']} old conversations")
            Cleaned 150 old conversations
        """
        try:
            from datetime import timedelta
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cutoff_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                cutoff_date = cutoff_date - timedelta(days=days_to_keep)
                cutoff_str = cutoff_date.isoformat()
                
                cleaned = {}
                
                # Clean up old conversations
                cursor.execute("""
                    DELETE FROM conversation_history 
                    WHERE timestamp < ?
                """, (cutoff_str,))
                cleaned["conversations"] = cursor.rowcount
                
                # Clean up old metrics
                cursor.execute("""
                    DELETE FROM agent_metrics 
                    WHERE timestamp < ?
                """, (cutoff_str,))
                cleaned["metrics"] = cursor.rowcount
                
                # Clean up old sessions
                cursor.execute("""
                    DELETE FROM agent_sessions 
                    WHERE ended_at IS NOT NULL AND ended_at < ?
                """, (cutoff_str,))
                cleaned["sessions"] = cursor.rowcount
                
                conn.commit()
                
                logger.info(f"Cleaned up old data: {cleaned}")
                return cleaned
                
        except sqlite3.Error as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return {"error": str(e)}
    
    def optimize_database(self) -> bool:
        """Optimize the database for better performance.
        
        Returns:
            bool: True if successful, False otherwise.
            
        Example:
            >>> storage = AgentStorageManager()
            >>> success = storage.optimize_database()
            >>> print("Database optimized" if success else "Failed")
            Database optimized
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Analyze tables for better query planning
                conn.execute("ANALYZE")
                
                # Vacuum to reclaim space
                conn.execute("VACUUM")
                
                conn.commit()
                logger.info("Database optimized successfully")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Failed to optimize database: {e}")
            return False
    
    def validate_data_integrity(self) -> Dict[str, Any]:
        """Validate data integrity in the database.
        
        Returns:
            Dict[str, Any]: Validation results and any issues found.
            
        Example:
            >>> storage = AgentStorageManager()
            >>> validation = storage.validate_data_integrity()
            >>> print(f"Validation: {validation['status']}")
            Validation: passed
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                issues = []
                
                # Check for orphaned records
                cursor.execute("""
                    SELECT COUNT(*) FROM agent_sessions 
                    WHERE agent_id NOT IN (SELECT agent_id FROM agents)
                """)
                orphaned_sessions = cursor.fetchone()[0]
                if orphaned_sessions > 0:
                    issues.append(f"Found {orphaned_sessions} orphaned agent sessions")
                
                cursor.execute("""
                    SELECT COUNT(*) FROM conversation_history 
                    WHERE session_id NOT IN (SELECT session_id FROM agent_sessions)
                """)
                orphaned_conversations = cursor.fetchone()[0]
                if orphaned_conversations > 0:
                    issues.append(f"Found {orphaned_conversations} orphaned conversations")
                
                # Check for invalid JSON in text fields
                cursor.execute("SELECT agent_id, agent_name FROM agents")
                for agent_id, agent_name in cursor.fetchall():
                    try:
                        cursor.execute("SELECT agent_config FROM agents WHERE agent_id = ?", (agent_id,))
                        config_json = cursor.fetchone()[0]
                        if config_json:
                            json.loads(config_json)
                    except json.JSONDecodeError:
                        issues.append(f"Invalid JSON in agent_config for agent {agent_name}")
                
                return {
                    "status": "passed" if not issues else "failed",
                    "issues": issues,
                    "checked_at": datetime.utcnow().isoformat()
                }
                
        except sqlite3.Error as e:
            logger.error(f"Failed to validate data integrity: {e}")
            return {"status": "error", "error": str(e)}
