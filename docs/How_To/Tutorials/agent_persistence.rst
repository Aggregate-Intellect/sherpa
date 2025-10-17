Agent Persistence with Sherpa
==============================

Agent persistence allows you to save and restore agents across sessions, maintaining their state and configuration. Sherpa AI provides a comprehensive persistence system with multi-user support and flexible storage backends.

Basic Agent Persistence
***********************

The ``PersistentAgentPool`` allows you to save agents to storage and restore them later, maintaining their configuration and state. This is essential for applications that need to persist agent instances across application restarts or share agents between different sessions.

Let's create and save an agent:

.. code-block:: python

    from sherpa_ai.agents.persistent_agent_pool import PersistentAgentPool
    from sherpa_ai.agents.qa_agent import QAAgent
    
    # Create persistent pool
    pool = PersistentAgentPool("my_agents.db", "sqlite")
    
    # Create and save an agent
    agent = QAAgent(name="My Assistant", description="A helpful QA agent")
    agent_id = pool.save_agent(agent, user_id="user123")
    
    # Load agent later
    loaded_agent = pool.get_agent(agent_id)
    print(f"Loaded: {loaded_agent.name}")

User Management
***************

The ``UserAgentManager`` provides multi-user support with isolated agent spaces, user preferences, and session tracking. This enables applications to support multiple users where each user can have their own set of agents with personalized settings and usage limits.

For multi-user applications, use the UserAgentManager:

.. code-block:: python

    from sherpa_ai.agents.user_agent_manager import UserAgentManager
    
    # Create user manager
    manager = UserAgentManager("user_agents.db")
    
    # Create user and agent
    manager.create_user("user123", max_agents=5)
    agent_id = manager.create_agent_for_user("user123", "My Assistant", "QAAgent")
    
    # Start session and use agent
    session_id = manager.start_user_session("user123", "My Assistant")
    agent = manager.get_agent_for_user("user123", "My Assistant")
    result = agent.synthesize_output()
    manager.end_user_session(session_id)

Storage Backends
****************

Sherpa supports two storage backends for agent persistence, each optimized for different use cases. SQLite provides robust database functionality with ACID compliance and concurrent access, while JSON offers simplicity for development and single-user scenarios.

**SQLite (Recommended for production):**

.. code-block:: python

    pool = PersistentAgentPool("agents.db", "sqlite")

**JSON (Good for development):**

.. code-block:: python

    pool = PersistentAgentPool("agents.json", "json")

Setup and Configuration
***********************

Choose your persistence setup based on your application needs. For simple single-user applications, use the basic ``PersistentAgentPool``. For multi-user applications with user management, use the ``UserAgentManager`` which provides additional features like user preferences and session tracking.

**Basic Setup (Single User):**

.. code-block:: python

    from sherpa_ai.agents.persistent_agent_pool import PersistentAgentPool
    
    # Choose storage backend
    pool = PersistentAgentPool("my_agents.db", "sqlite")  # or "json"
    
    # Save and load agents
    agent_id = pool.save_agent(agent, user_id="default")
    loaded_agent = pool.get_agent(agent_id)

**Multi-User Setup:**

.. code-block:: python

    from sherpa_ai.agents.user_agent_manager import UserAgentManager
    
    # Initialize with database
    manager = UserAgentManager("user_agents.db")
    
    # Create users with custom preferences
    manager.create_user("user1", max_agents=10, auto_save=True)
    manager.create_user("user2", max_agents=5, default_agent_type="QAAgent")
    
    # Create agents for specific users
    agent_id = manager.create_agent_for_user("user1", "Assistant", "QAAgent")

The persistence system supports multi-user isolation, session tracking, and flexible storage options. For detailed API reference, see :doc:`API Documentation <../API_Docs/sherpa_ai.agents>`.
