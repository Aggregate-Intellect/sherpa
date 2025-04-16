sherpa\_ai.memory package
=========================

Overview
--------

The ``memory`` package provides persistence and knowledge management capabilities for Sherpa AI agents, enabling them to retain information across sessions and share knowledge between different components.

.. admonition:: Key Components
   :class: note
   
   * **Belief**: Structures for representing agent beliefs and knowledge
   * **SharedMemory**: Mechanisms for sharing information between agents
   * **Knowledge Management**: Tools for organizing and retrieving stored information

Example Usage
-------------

.. code-block:: python

   from sherpa_ai.memory.shared_memory import SharedMemory
   from sherpa_ai.memory.belief import Belief
   
   # Create a shared memory instance
   memory = SharedMemory()
   
   # Create and store a belief
   belief = Belief(
       content="The Earth orbits the Sun.",
       source="Astronomy facts",
       confidence=0.99
   )
   
   # Add the belief to memory
   memory.add_belief(belief)
   
   # Retrieve beliefs on a topic
   astronomy_beliefs = memory.get_beliefs_by_topic("astronomy")
   print(f"Found {len(astronomy_beliefs)} beliefs about astronomy")

Submodules
----------

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Module
     - Description
   * - :mod:`sherpa_ai.memory.belief`
     - Provides the Belief class for representing and managing agent knowledge.
   * - :mod:`sherpa_ai.memory.shared_memory`
     - Implements the SharedMemory system for knowledge persistence and sharing.

.. toctree::
   :hidden:

   sherpa_ai.memory.belief
   sherpa_ai.memory.shared_memory

sherpa\_ai.memory.belief module
-------------------------------

.. automodule:: sherpa_ai.memory.belief
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.memory.shared\_memory module
---------------------------------------

.. automodule:: sherpa_ai.memory.shared_memory
   :members:
   :undoc-members:
   :show-inheritance:

Module contents
---------------

.. automodule:: sherpa_ai.memory
   :members:
   :undoc-members:
   :show-inheritance: