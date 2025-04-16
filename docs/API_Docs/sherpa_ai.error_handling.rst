sherpa\_ai.error\_handling package
==================================

Overview
--------

The ``error_handling`` package provides robust error management capabilities for Sherpa AI applications, ensuring graceful recovery from failures and maintaining system stability during agent operations.

.. admonition:: Key Components
   :class: note
   
   * **AgentErrorHandler**: Manages and handles errors occurring in agent operations
   * **Error Classification**: Categorizes errors for appropriate handling strategies
   * **Recovery Mechanisms**: Techniques for recovering from various error types

Example Usage
-------------

.. code-block:: python

   from sherpa_ai.error_handling.agent_error_handler import AgentErrorHandler
   from sherpa_ai.agents import QAAgent
   
   # Create an error handler
   error_handler = AgentErrorHandler()
   
   # Use with an agent in a try-except block
   try:
       agent = QAAgent()
       response = agent.get_response("What is quantum computing?")
   except Exception as e:
       # Handle the error
       handled_response = error_handler.handle(e, fallback_msg="I couldn't process your request.")
       print(handled_response)

Submodules
----------

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Module
     - Description
   * - :mod:`sherpa_ai.error_handling.agent_error_handler`
     - Provides the AgentErrorHandler class for managing and recovering from errors.

.. toctree::
   :hidden:

   sherpa_ai.error_handling.agent_error_handler

sherpa\_ai.error\_handling.agent\_error\_handler module
-------------------------------------------------------

.. automodule:: sherpa_ai.error_handling.agent_error_handler
   :members:
   :undoc-members:
   :show-inheritance:

Module contents
---------------

.. automodule:: sherpa_ai.error_handling
   :members:
   :undoc-members:
   :show-inheritance: