sherpa\_ai.actions package
==========================

Overview
--------

The ``actions`` package contains a collection of specialized actions that Sherpa AI agents can perform to accomplish tasks. These actions range from web searches to mathematical operations and content synthesis.

.. admonition:: Key Components
   :class: note
   
   * **Web Interactions**: Google and arXiv search capabilities
   * **Reasoning Actions**: Deliberation and planning mechanisms
   * **Content Processing**: Context search and synthesis operations
   * **Mathematical Tools**: Arithmetic problem-solving actions

Example Usage
-------------

.. code-block:: python

   from sherpa_ai.actions import GoogleSearch, Synthesize
   
   # Perform a Google search
   search_action = GoogleSearch()
   search_results = search_action.run("latest developments in quantum computing")
   
   # Synthesize information from search results
   synthesize_action = Synthesize()
   summary = synthesize_action.run(context=search_results)
   
   print(summary)

Submodules
----------

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Module
     - Description
   * - :mod:`sherpa_ai.actions.arxiv_search`
     - Implements search capabilities for academic papers and research on arXiv.
   * - :mod:`sherpa_ai.actions.base`
     - Contains the abstract base classes that define the action interface.
   * - :mod:`sherpa_ai.actions.context_search`
     - Offers tools for searching within provided context or documents.
   * - :mod:`sherpa_ai.actions.deliberation`
     - Provides reasoning and reflection capabilities for decision-making.
   * - :mod:`sherpa_ai.actions.google_search`
     - Implements web search functionality using Google search engine.
   * - :mod:`sherpa_ai.actions.planning`
     - Contains actions for creating plans and strategic action sequences.
   * - :mod:`sherpa_ai.actions.synthesize`
     - Offers capabilities for generating summaries and synthesizing information.

.. toctree::
   :hidden:

   sherpa_ai.actions.arxiv_search
   sherpa_ai.actions.base
   sherpa_ai.actions.context_search
   sherpa_ai.actions.deliberation
   sherpa_ai.actions.google_search
   sherpa_ai.actions.planning
   sherpa_ai.actions.synthesize


sherpa\_ai.actions.arxiv\_search module
---------------------------------------

.. automodule:: sherpa_ai.actions.arxiv_search
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.actions.base module
------------------------------

.. automodule:: sherpa_ai.actions.base
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.actions.context\_search module
-----------------------------------------

.. automodule:: sherpa_ai.actions.context_search
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.actions.deliberation module
--------------------------------------

.. automodule:: sherpa_ai.actions.deliberation
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.actions.google\_search module
----------------------------------------

.. automodule:: sherpa_ai.actions.google_search
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.actions.planning module
----------------------------------

.. automodule:: sherpa_ai.actions.planning
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.actions.synthesize module
------------------------------------

.. automodule:: sherpa_ai.actions.synthesize
   :members:
   :undoc-members:
   :show-inheritance:

Module contents
---------------

.. automodule:: sherpa_ai.actions
   :members:
   :undoc-members:
   :show-inheritance:
