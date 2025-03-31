sherpa\_ai package
==================

Overview
--------

The ``sherpa_ai`` package is a comprehensive AI framework for building intelligent, multi-agent systems that can tackle complex problems through strategic planning, reasoning, and collaboration. It provides a complete ecosystem of agents, actions, planners, and memory systems that can be combined and customized for various applications.

.. admonition:: Key Components
   :class: tip
   
   * **Agents**: Domain-specific AI agents with different expertise and capabilities
   * **Actions**: Specialized operations that agents can perform to accomplish tasks
   * **Policies**: Decision-making strategies for agent behavior and reasoning
   * **Memory Systems**: Persistent storage for knowledge, beliefs, and conversation history
   * **Models**: Interfaces with various LLM providers with enhanced logging and error handling
   * **Prompts**: Template-based system for creating and managing prompts for language models
   * **Tools**: Utility functions and interfaces for common AI operations
   * **Reflection**: Capabilities for self-evaluation and improvement
   * **Events**: Event-driven architecture for coordinating system components
   * **Test Utilities**: Testing tools for data, language models, and logging

Installation
------------

The Sherpa AI package can be installed via pip:

.. code-block:: bash

   pip install sherpa-ai


Subpackages
-----------

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Package
     - Description
   * - :mod:`sherpa_ai.actions`
     - Collection of specialized actions that agents can perform to accomplish tasks.
   * - :mod:`sherpa_ai.agents`
     - Specialized AI agents with different roles and expertise for various domains.
   * - :mod:`sherpa_ai.config`
     - Configuration management tools for customizing system behavior.
   * - :mod:`sherpa_ai.connectors`
     - Interfaces for connecting to external systems and databases.
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
   * - :mod:`sherpa_ai.policies`
     - Decision-making strategies for agents to handle different scenarios.
   * - :mod:`sherpa_ai.prompts`
     - Template-based system for creating, loading, and formatting prompts.
   * - :mod:`sherpa_ai.scrape`
     - Utilities for extracting information from files and repositories.
   * - :mod:`sherpa_ai.test_utils`
     - Testing utilities for data, language models, and logging.
   * - :mod:`sherpa_ai.verbose_loggers`
     - Advanced logging capabilities for debugging and monitoring.

.. toctree::
   :maxdepth: 4
   :hidden:

   sherpa_ai.actions
   sherpa_ai.agents
   sherpa_ai.config
   sherpa_ai.connectors
   sherpa_ai.database
   sherpa_ai.error_handling
   sherpa_ai.memory
   sherpa_ai.models
   sherpa_ai.output_parsers
   sherpa_ai.policies
   sherpa_ai.prompts
   sherpa_ai.scrape
   sherpa_ai.test_utils
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
   * - :mod:`sherpa_ai.tools`
     - Utility functions and tools for common AI operations.
   * - :mod:`sherpa_ai.utils`
     - General utility functions used throughout the framework.

.. toctree::
   :hidden:

   sherpa_ai.events
   sherpa_ai.output_parser
   sherpa_ai.post_processors
   sherpa_ai.prompt
   sherpa_ai.prompt_generator
   sherpa_ai.reflection
   sherpa_ai.tools
   sherpa_ai.utils

sherpa\_ai.events module
------------------------

.. automodule:: sherpa_ai.events
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
