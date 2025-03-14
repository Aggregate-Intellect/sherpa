sherpa\_ai.action\_planner package
==================================

Overview
--------

The ``action_planner`` package provides strategic planning capabilities for Sherpa AI agents, allowing them to generate and execute sequences of actions to accomplish complex tasks.

.. admonition:: Key Components
   :class: note
   
   * **ActionPlanner**: Core planning interface used to coordinate action sequences
   * **SelectivePlanner**: Intelligent planner that selectively chooses appropriate actions
   * **SimplePlanner**: Streamlined planner for straightforward action sequences
   * **Base**: Abstract base classes defining the planner interface

Example Usage
------------

.. code-block:: python

   from sherpa_ai.action_planner import SimplePlanner
   from sherpa_ai.actions import GoogleSearch, Synthesize
   
   # Create a planner with available actions
   planner = SimplePlanner(actions=[GoogleSearch(), Synthesize()])
   
   # Generate a plan for a query
   plan = planner.plan("What are the latest developments in AI?")
   
   # Execute the plan
   results = planner.execute(plan)

Submodules
----------

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Module
     - Description
   * - :mod:`sherpa_ai.action_planner.action_planner`
     - Implements the core ActionPlanner class that coordinates planning activities.
   * - :mod:`sherpa_ai.action_planner.base`
     - Contains abstract base classes and interfaces that define the planner architecture.
   * - :mod:`sherpa_ai.action_planner.selective_planner`
     - Provides the SelectivePlanner implementation that intelligently selects optimal actions.
   * - :mod:`sherpa_ai.action_planner.simple_planner`
     - Implements a straightforward SimplePlanner for basic action sequencing needs.

.. toctree::
   :hidden:

   sherpa_ai.action_planner.action_planner
   sherpa_ai.action_planner.base
   sherpa_ai.action_planner.selective_planner
   sherpa_ai.action_planner.simple_planner

