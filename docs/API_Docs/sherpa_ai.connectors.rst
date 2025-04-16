sherpa\_ai.connectors package
==========================

Overview
--------

The ``connectors`` package provides interfaces for Sherpa AI to connect with external systems
and databases. It includes specialized connectors for vector stores and other data persistence
mechanisms required for retrieval-augmented generation and knowledge storage.

.. admonition:: Key Components
   :class: note
   
   * **Base**: Abstract interface for connector implementations
   * **ChromaVectorStore**: Implementation for the Chroma vector database
   * **VectorStores**: Generic interfaces for vector database interactions

Example Usage
-------------

.. code-block:: python

   from sherpa_ai.connectors.chroma_vector_store import ChromaVectorStore
   
   # Initialize a vector store
   vector_store = ChromaVectorStore(
       collection_name="documents",
       embedding_function=embedding_fn
   )
   
   # Store documents
   documents = [
       "Sherpa AI is a framework for building intelligent agents.",
       "Vector databases store vector embeddings for semantic search."
   ]
   vector_store.add_texts(documents, metadatas=[{"source": "docs"} for _ in documents])
   
   # Retrieve similar documents
   results = vector_store.similarity_search("How do I build an agent?", k=2)
   print(results)

Submodules
----------

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Module
     - Description
   * - :mod:`sherpa_ai.connectors.base`
     - Abstract base classes defining the connector interface.
   * - :mod:`sherpa_ai.connectors.chroma_vector_store`
     - Implementation for the Chroma vector database with document storage.
   * - :mod:`sherpa_ai.connectors.vectorstores`
     - Generic interfaces and utilities for vector database interactions.

.. toctree::
   :hidden:

   sherpa_ai.connectors.base
   sherpa_ai.connectors.chroma_vector_store
   sherpa_ai.connectors.vectorstores

sherpa\_ai.connectors.base module
--------------------------------

.. automodule:: sherpa_ai.connectors.base
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.connectors.chroma\_vector\_store module
------------------------------------------------

.. automodule:: sherpa_ai.connectors.chroma_vector_store
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.connectors.vectorstores module
---------------------------------------

.. automodule:: sherpa_ai.connectors.vectorstores
   :members:
   :undoc-members:
   :show-inheritance:

Module contents
--------------

.. automodule:: sherpa_ai.connectors
   :members:
   :undoc-members:
   :show-inheritance: 