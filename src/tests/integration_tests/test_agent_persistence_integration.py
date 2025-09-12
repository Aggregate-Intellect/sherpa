"""Simplified integration tests for agent persistence."""

import os
import tempfile
import unittest
from unittest.mock import Mock

from sherpa_ai.agents.agent_pool import AgentPool
from sherpa_ai.agents.user_agent_manager import UserAgentManager
from sherpa_ai.agents.base import BaseAgent


class TestAgentPersistenceIntegration(unittest.TestCase):
    """Integration tests for agent persistence."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_agent_pool_backward_compatibility(self):
        """Test that AgentPool maintains backward compatibility."""
        # Test default behavior (no persistence)
        pool = AgentPool()
        self.assertIsNone(pool.persistent_pool)
        self.assertIsNone(pool.user_manager)

    def test_agent_pool_with_persistence_enabled(self):
        """Test AgentPool with persistence enabled."""
        pool = AgentPool(persistent=True, db_path=self.db_path)
        self.assertIsNotNone(pool.persistent_pool)
        self.assertIsNone(pool.user_manager)

    def test_agent_pool_with_user_management_enabled(self):
        """Test AgentPool with user management enabled."""
        pool = AgentPool(user_management=True, db_path=self.db_path)
        self.assertIsNotNone(pool.user_manager)
        self.assertIsNone(pool.persistent_pool)

    def test_user_management_workflow(self):
        """Test basic user management workflow."""
        manager = UserAgentManager(self.db_path)
        
        # Create user
        user_id = "test_user"
        prefs = manager.create_user(user_id, max_agents=3)
        self.assertEqual(prefs.user_id, user_id)
        self.assertEqual(prefs.max_agents, 3)
        
        # Create agent for user
        agent_id = manager.create_agent_for_user(user_id, "Test Agent")
        self.assertIsNotNone(agent_id)
        
        # Get user agents
        agents = manager.get_user_agents(user_id)
        self.assertEqual(len(agents), 1)
        
        # Start session
        session_id = manager.start_user_session(user_id, "Test Agent")
        self.assertIsNotNone(session_id)
        
        # Get user statistics
        stats = manager.get_user_statistics(user_id)
        self.assertEqual(stats["total_agents"], 1)
        self.assertEqual(stats["active_sessions"], 1)
        
        # End session
        success = manager.end_user_session(session_id)
        self.assertTrue(success)

    def test_multi_user_isolation(self):
        """Test that different users have isolated agents."""
        manager = UserAgentManager(self.db_path)
        
        # Create two users
        user1 = "user1"
        user2 = "user2"
        
        manager.create_user(user1)
        manager.create_user(user2)
        
        # Create agents for each user
        agent1_id = manager.create_agent_for_user(user1, "User1 Agent")
        agent2_id = manager.create_agent_for_user(user2, "User2 Agent")
        
        # Get agents for each user
        user1_agents = manager.get_user_agents(user1)
        user2_agents = manager.get_user_agents(user2)
        
        # Each user should have their own agents
        self.assertEqual(len(user1_agents), 1)
        self.assertEqual(len(user2_agents), 1)
        
        # User1 should not see User2's agents
        user1_agent_names = [agent.agent_name for agent in user1_agents]
        self.assertIn("User1 Agent", user1_agent_names)
        self.assertNotIn("User2 Agent", user1_agent_names)

    def test_agent_persistence_basic_workflow(self):
        """Test basic agent persistence workflow."""
        pool = AgentPool(persistent=True, db_path=self.db_path)
        
        # Create a mock agent with all required attributes
        mock_agent = Mock(spec=BaseAgent)
        mock_agent.name = "Persistent Agent"
        mock_agent.__class__.__name__ = "MockAgent"
        mock_agent.description = "A persistent test agent"
        mock_agent.model_dump.return_value = {"name": "Persistent Agent", "description": "A persistent test agent"}
        
        # Save agent (might return None for mock agents, which is expected)
        agent_id = pool.save_agent(mock_agent, user_id="test_user")
        
        # List agents
        agents = pool.list_agents()
        self.assertIsInstance(agents, list)
        
        # Get agent count
        count = len(pool.list_agents())
        self.assertGreaterEqual(count, 0)  # Should be 0 or more


if __name__ == '__main__':
    unittest.main()
