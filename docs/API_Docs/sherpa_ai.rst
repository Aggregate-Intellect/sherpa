sherpa\_ai package
==================

Overview
--------

The ``sherpa_ai`` package is a comprehensive AI framework for building intelligent, multi-agent systems that can tackle complex problems through strategic planning, reasoning, and collaboration. It provides a complete ecosystem of agents, actions, planners, and memory systems that can be combined and customized for various applications.

.. admonition:: Key Components
   :class: tip
   
   * **Orchestrator**: Coordinates the flow of information between agents and manages the execution of tasks
   * **Task Agent**: Specialized agent for handling specific user tasks and generating appropriate responses
   * **Action Planners**: Creates and executes strategic sequences of actions to accomplish goals
   * **Agents**: Domain-specific AI agents with different expertise and capabilities
   * **Memory Systems**: Persistent storage for knowledge, beliefs, and conversation history
   * **Models**: Interfaces with various LLM providers with enhanced logging and error handling
   * **Tools**: Utility functions and interfaces for common AI operations
   * **Reflection**: Capabilities for self-evaluation and improvement
   * **Events**: Event-driven architecture for coordinating system components

Installation
-----------

The Sherpa AI package can be installed via pip:

.. code-block:: bash

   pip install sherpa-ai

Quick Usage
----------

.. code-block:: python

   # Basic orchestrated multi-agent system
   from sherpa_ai.orchestrator import Orchestrator
   from sherpa_ai.agents import QAAgent, Critic
   from sherpa_ai.models import SherpaBaseChatModel
   
   # Initialize models and agents
   model = SherpaBaseChatModel(model_name="gpt-4")
   qa_agent = QAAgent(model=model)
   critic = Critic(model=model)
   
   # Create an orchestrator with multiple agents
   orchestrator = Orchestrator(
       agents=[qa_agent, critic],
       primary_agent=qa_agent
   )
   
   # Process a user query
   result = orchestrator.process("Explain how neural networks learn through backpropagation")
   
   print(result)

Advanced Usage
-------------

.. code-block:: python

   # Advanced system with memory and action planning
   from sherpa_ai.orchestrator import Orchestrator
   from sherpa_ai.agents import QAAgent
   from sherpa_ai.memory import SharedMemory
   from sherpa_ai.action_planner import SimplePlanner
   from sherpa_ai.actions import GoogleSearch, Synthesize
   
   # Set up memory
   memory = SharedMemory()
   
   # Set up action planner with actions
   planner = SimplePlanner(actions=[
       GoogleSearch(),
       Synthesize()
   ])
   
   # Create agent with memory and planner
   agent = QAAgent(memory=memory, action_planner=planner)
   
   # Create orchestrator
   orchestrator = Orchestrator(agents=[agent])
   
   # Process queries with memory persistence
   orchestrator.process("What are quantum computers?")
   
   # The next query can reference previous interactions
   orchestrator.process("How do they compare to classical computers?")

Subpackages
-----------

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Package
     - Description
   * - :mod:`sherpa_ai.action_planner`
     - Strategic planning capabilities for generating and executing action sequences.
   * - :mod:`sherpa_ai.actions`
     - Collection of specialized actions that agents can perform to accomplish tasks.
   * - :mod:`sherpa_ai.agents`
     - Specialized AI agents with different roles and expertise for various domains.
   * - :mod:`sherpa_ai.config`
     - Configuration management tools for customizing system behavior.
   * - :mod:`sherpa_ai.database`
     - Database interaction capabilities for persistence and analytics.
   * - :mod:`sherpa_ai.error_handling`
     - Error management tools for recovery and stability.
   * - :mod:`sherpa_ai.memory`
     - Knowledge persistence and sharing across sessions and components.
   * - :mod:`sherpa_ai.models`
     - Interfaces with language model providers and enhanced model functionality.
   * - :mod:`sherpa_ai.output_parsers`
     - Tools for validating and transforming model outputs.
   * - :mod:`sherpa_ai.verbose_loggers`
     - Advanced logging capabilities for debugging and monitoring.

.. toctree::
   :maxdepth: 4
   :hidden:

   sherpa_ai.action_planner
   sherpa_ai.actions
   sherpa_ai.agents
   sherpa_ai.config
   sherpa_ai.database
   sherpa_ai.error_handling
   sherpa_ai.memory
   sherpa_ai.models
   sherpa_ai.output_parsers
   sherpa_ai.verbose_loggers

Submodules
----------

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Module
     - Description
   * - :mod:`sherpa_ai.events`
     - Event system for coordinating component interactions and message passing.
   * - :mod:`sherpa_ai.orchestrator`
     - Core orchestration engine that coordinates agents and manages workflow.
   * - :mod:`sherpa_ai.output_parser`
     - Tools for parsing and processing model outputs into usable formats.
   * - :mod:`sherpa_ai.post_processors`
     - Processes model outputs for additional formatting and enhancement.
   * - :mod:`sherpa_ai.prompt`
     - Tools for creating and managing prompts for language models.
   * - :mod:`sherpa_ai.prompt_generator`
     - Dynamic prompt generation based on context and requirements.
   * - :mod:`sherpa_ai.reflection`
     - Self-evaluation and improvement capabilities for agents.
   * - :mod:`sherpa_ai.task_agent`
     - Specialized agent for handling specific user tasks.
   * - :mod:`sherpa_ai.tools`
     - Utility functions and tools for common AI operations.
   * - :mod:`sherpa_ai.utils`
     - General utility functions used throughout the framework.

.. toctree::
   :hidden:

   sherpa_ai.events
   sherpa_ai.orchestrator
   sherpa_ai.output_parser
   sherpa_ai.post_processors
   sherpa_ai.prompt
   sherpa_ai.prompt_generator
   sherpa_ai.reflection
   sherpa_ai.task_agent
   sherpa_ai.tools
   sherpa_ai.utils

sherpa\_ai.events module
------------------------

.. automodule:: sherpa_ai.events
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.orchestrator module
------------------------------

.. automodule:: sherpa_ai.orchestrator
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.output\_parser module
--------------------------------

.. automodule:: sherpa_ai.output_parser
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.post\_processors module
----------------------------------

.. automodule:: sherpa_ai.post_processors
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.prompt module
------------------------

.. automodule:: sherpa_ai.prompt
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.prompt\_generator module
-----------------------------------

.. automodule:: sherpa_ai.prompt_generator
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.reflection module
----------------------------

.. automodule:: sherpa_ai.reflection
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.task\_agent module
-----------------------------

.. automodule:: sherpa_ai.task_agent
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.tools module
-----------------------

.. automodule:: sherpa_ai.tools
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.utils module
-----------------------

.. automodule:: sherpa_ai.utils
   :members:
   :undoc-members:
   :show-inheritance:

Module contents
---------------

.. automodule:: sherpa_ai
   :members:
   :undoc-members:
   :show-inheritance:
