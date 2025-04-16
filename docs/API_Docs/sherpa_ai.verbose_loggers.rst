sherpa\_ai.verbose\_loggers package
===================================

Overview
--------

The ``verbose_loggers`` package provides advanced logging capabilities for Sherpa AI, enabling detailed tracking and visualization of agent operations, model interactions, and system events.

.. admonition:: Key Components
   :class: note
   
   * **BaseVerboseLogger**: Core logging interface that defines the logging protocol
   * **Specialized Loggers**: Various logger implementations for different logging needs
   * **Formatting Tools**: Utilities for formatting and presenting log information

Example Usage
-------------

.. code-block:: python

   from sherpa_ai.verbose_loggers import ConsoleLogger
   from sherpa_ai.orchestrator import Orchestrator
   from sherpa_ai.agents import QAAgent
   
   # Create a logger
   logger = ConsoleLogger(log_level="INFO")
   
   # Create an agent with verbose logging
   agent = QAAgent(verbose_logger=logger)
   
   # Create an orchestrator with the agent
   orchestrator = Orchestrator(agents=[agent], verbose_logger=logger)
   
   # Process a query with detailed logging
   orchestrator.process("What is artificial intelligence?")

Submodules
----------

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Module
     - Description
   * - :mod:`sherpa_ai.verbose_loggers.base`
     - Contains the BaseVerboseLogger class that defines the core logging interface and protocols.
   * - :mod:`sherpa_ai.verbose_loggers.verbose_loggers`
     - Implements various logger types including console loggers, file loggers, and specialized formatters.

.. toctree::
   :hidden:

   sherpa_ai.verbose_loggers.base
   sherpa_ai.verbose_loggers.verbose_loggers

sherpa\_ai.verbose\_loggers.base module
---------------------------------------

.. automodule:: sherpa_ai.verbose_loggers.base
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.verbose\_loggers.verbose\_loggers module
---------------------------------------------------

.. automodule:: sherpa_ai.verbose_loggers.verbose_loggers
   :members:
   :undoc-members:
   :show-inheritance:

Module contents
---------------

.. automodule:: sherpa_ai.verbose_loggers
   :members:
   :undoc-members:
   :show-inheritance: