sherpa\_ai.config package
=========================

Overview
--------

The ``config`` package provides configuration management tools for Sherpa AI applications. It allows users to define and customize task-specific settings and parameters to control agent behavior.

.. admonition:: Key Components
   :class: note
   
   * **TaskConfig**: Configuration class for defining task-specific settings
   * **Configuration Management**: Tools for loading and saving configurations
   * **Parameter Validation**: Ensures configuration parameters are valid

Example Usage
-------------

.. code-block:: python

   from sherpa_ai.config import TaskConfig
   
   # Create a task configuration
   config = TaskConfig(
       task_name="Question Answering",
       model_name="gpt-4",
       temperature=0.7,
       max_tokens=1000
   )
   
   # Use the configuration with an agent
   from sherpa_ai.agents import QAAgent
   
   agent = QAAgent(config=config)
   response = agent.get_response("What is artificial intelligence?")

Submodules
----------

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Module
     - Description
   * - :mod:`sherpa_ai.config.task_config`
     - Provides the TaskConfig class for managing agent and task-specific configurations.

.. toctree::
   :hidden:

   sherpa_ai.config.task_config

sherpa\_ai.config.task\_config module
-------------------------------------

.. automodule:: sherpa_ai.config.task_config
   :members:
   :undoc-members:
   :show-inheritance:

Module contents
---------------

.. automodule:: sherpa_ai.config
   :members:
   :undoc-members:
   :show-inheritance:
