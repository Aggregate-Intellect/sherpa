sherpa\_ai.policies package
=======================

Overview
--------

The ``policies`` package provides decision-making strategies that agents use to handle different
scenarios and determine appropriate actions. It includes reactive and state machine-based policies
for various interaction patterns and reasoning approaches.

.. admonition:: Key Components
   :class: note
   
   * **Base Policy**: Abstract interface for all policy implementations
   * **React Policy**: Implementation of ReAct (Reasoning+Acting) pattern
   * **State Machine Policies**: Policies that use finite state machines for complex workflows
   * **Agent Feedback**: Policies for handling agent evaluation and improvement

Example Usage
-------------

.. code-block:: python

   from sherpa_ai.policies.react_policy import ReactPolicy
   from sherpa_ai.agents import QAAgent
   from sherpa_ai.models import SherpaBaseChatModel
   
   # Initialize a model
   model = SherpaBaseChatModel(model_name="gpt-4")
   
   # Create a ReactPolicy
   policy = ReactPolicy(
       max_iterations=5,
       tools=["search", "calculator"]
   )
   
   # Create an agent using this policy
   agent = QAAgent(model=model, policy=policy)
   
   # Process a query that requires reasoning and tool use
   result = agent.get_response("What is the square root of the population of France?")
   print(result)

Submodules
----------

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Module
     - Description
   * - :mod:`sherpa_ai.policies.agent_feedback_policy`
     - Policy for handling agent evaluation and improvement processes.
   * - :mod:`sherpa_ai.policies.base`
     - Abstract base classes defining the policy interface.
   * - :mod:`sherpa_ai.policies.chat_sm_policy`
     - Chat-based state machine policy for conversational workflows.
   * - :mod:`sherpa_ai.policies.exceptions`
     - Custom exceptions for policy-related error handling.
   * - :mod:`sherpa_ai.policies.react_policy`
     - Implementation of the ReAct (Reasoning+Acting) policy pattern.
   * - :mod:`sherpa_ai.policies.react_sm_policy`
     - State machine-based implementation of the ReAct pattern.
   * - :mod:`sherpa_ai.policies.utils`
     - Utility functions and helpers for policy implementations.

.. toctree::
   :hidden:

   sherpa_ai.policies.agent_feedback_policy
   sherpa_ai.policies.base
   sherpa_ai.policies.chat_sm_policy
   sherpa_ai.policies.exceptions
   sherpa_ai.policies.react_policy
   sherpa_ai.policies.react_sm_policy
   sherpa_ai.policies.utils

sherpa\_ai.policies.agent\_feedback\_policy module
-----------------------------------------------

.. automodule:: sherpa_ai.policies.agent_feedback_policy
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.policies.base module
-----------------------------

.. automodule:: sherpa_ai.policies.base
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.policies.chat\_sm\_policy module
----------------------------------------

.. automodule:: sherpa_ai.policies.chat_sm_policy
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.policies.exceptions module
----------------------------------

.. automodule:: sherpa_ai.policies.exceptions
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.policies.react\_policy module
-------------------------------------

.. automodule:: sherpa_ai.policies.react_policy
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.policies.react\_sm\_policy module
-----------------------------------------

.. automodule:: sherpa_ai.policies.react_sm_policy
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.policies.utils module
-----------------------------

.. automodule:: sherpa_ai.policies.utils
   :members:
   :undoc-members:
   :show-inheritance:

Module contents
--------------

.. automodule:: sherpa_ai.policies
   :members:
   :undoc-members:
   :show-inheritance: 