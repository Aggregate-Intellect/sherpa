sherpa\_ai.agents package
=========================

Overview
--------

The ``agents`` package provides specialized AI agents with different roles and capabilities. Each agent is designed to excel at specific types of tasks, from answering questions to planning complex workflows.

.. admonition:: Key Components
   :class: note
   
   * **QAAgent**: Specialized in question answering tasks
   * **MLEngineer**: Expert in machine learning tasks and code generation
   * **Physicist**: Specialized in physics-related questions and calculations
   * **Planner**: Creates strategic plans for complex problems
   * **Critic**: Evaluates and provides feedback on other agents' outputs
   * **AgentPool**: Manages multiple agents and their interactions
   * **PersistentAgentPool**: Enhanced agent pool with persistence capabilities
   * **UserAgentManager**: Multi-user agent management with preferences

Class Hierarchy
---------------

The following diagram shows the inheritance relationships between the core agent classes:

.. inheritance-diagram:: sherpa_ai.agents.base sherpa_ai.agents.qa_agent sherpa_ai.agents.critic sherpa_ai.agents.ml_engineer sherpa_ai.agents.physicist sherpa_ai.agents.planner
   :parts: 1
   :caption: Agent Class Hierarchy

Component Relationships
-----------------------

The diagram below shows how agents interact with other components of the Sherpa AI framework:

.. graphviz::
   :caption: Agent Component Relationships
   :align: center

   digraph "Agent Relationships" {
      graph [fontname="Helvetica", fontsize=14, rankdir=LR, nodesep=0.8, ranksep=0.8];
      node [fontname="Helvetica", fontsize=12, shape=box, style="filled,rounded", fillcolor="#f5f5f5", color="#336790", margin=0.3];
      edge [fontname="Helvetica", fontsize=10, color="#555555"];

      Agent [fillcolor="#d5f5e3", label="Agent"];
      Model [fillcolor="#fadbd8", label="Model"];
      Memory [fillcolor="#ebdef0", label="Memory"];
      Policy [fillcolor="#fdebd0", label="Policy"];
      Tools [fillcolor="#d6eaf8", label="Tools"];
      
      Agent -> Model [label="uses"];
      Agent -> Memory [label="reads/writes"];
      Agent -> Policy [label="follows"];
      Agent -> Tools [label="utilizes"];
   }

Example Usage
-------------

Basic Agent Usage
^^^^^^^^^^^^^^^^^

.. code-block:: python

   from sherpa_ai.agents import QAAgent, Critic
   from sherpa_ai.models import SherpaBaseChatModel
   
   # Create a QA agent
   model = SherpaBaseChatModel()
   qa_agent = QAAgent(model=model)
   
   # Get a response from the QA agent
   response = qa_agent.get_response("What is machine learning?")
   
   # Create a critic to evaluate the response
   critic = Critic(model=model)
   evaluation = critic.evaluate(response)
   
   print(f"Response: {response}")
   print(f"Evaluation: {evaluation}")

Agent Persistence
^^^^^^^^^^^^^^^^^

.. code-block:: python

   from sherpa_ai.agents.persistent_agent_pool import PersistentAgentPool
   from sherpa_ai.agents.user_agent_manager import UserAgentManager
   
   # Create persistent agent pool
   pool = PersistentAgentPool("agents.db", "sqlite")
   
   # Save an agent
   agent_id = pool.save_agent(qa_agent, user_id="user123")
   
   # Load agent later
   loaded_agent = pool.get_agent(agent_id)
   
   # Multi-user management
   manager = UserAgentManager("user_agents.db")
   manager.create_user("user123", max_agents=5)
   agent_id = manager.create_agent_for_user("user123", "My Assistant", "QAAgent")

Submodules
----------

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Module
     - Description
   * - :mod:`sherpa_ai.agents.agent_pool`
     - Provides the AgentPool class for managing multiple agents and their interactions.
   * - :mod:`sherpa_ai.agents.persistent_agent_pool`
     - Enhanced agent pool with persistence capabilities for saving and loading agents.
   * - :mod:`sherpa_ai.agents.user_agent_manager`
     - Multi-user agent management with preferences and session tracking.
   * - :mod:`sherpa_ai.agents.agent_storage`
     - Database schema management and migration utilities for agent persistence.
   * - :mod:`sherpa_ai.agents.base`
     - Contains abstract base classes defining the agent interface and core functionality.
   * - :mod:`sherpa_ai.agents.qa_agent`
     - Implements the QAAgent specialized in question answering tasks.
   * - :mod:`sherpa_ai.agents.user`
     - Provides the User agent that represents human users in the system.

.. toctree::
   :hidden:

   sherpa_ai.agents.agent_pool
   sherpa_ai.agents.persistent_agent_pool
   sherpa_ai.agents.user_agent_manager
   sherpa_ai.agents.agent_storage
   sherpa_ai.agents.base
   sherpa_ai.agents.qa_agent
   sherpa_ai.agents.user

sherpa\_ai.agents.agent\_pool module
------------------------------------

.. automodule:: sherpa_ai.agents.agent_pool
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.agents.persistent\_agent\_pool module
------------------------------------------------

.. automodule:: sherpa_ai.agents.persistent_agent_pool
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.agents.user\_agent\_manager module
---------------------------------------------

.. automodule:: sherpa_ai.agents.user_agent_manager
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.agents.agent\_storage module
---------------------------------------

.. automodule:: sherpa_ai.agents.agent_storage
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.agents.base module
-----------------------------

.. automodule:: sherpa_ai.agents.base
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.agents.qa\_agent module
----------------------------------

.. automodule:: sherpa_ai.agents.qa_agent
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.agents.user module
-----------------------------

.. automodule:: sherpa_ai.agents.user
   :members:
   :undoc-members:
   :show-inheritance:

Module contents
---------------

.. automodule:: sherpa_ai.agents
   :members:
   :undoc-members:
   :show-inheritance: