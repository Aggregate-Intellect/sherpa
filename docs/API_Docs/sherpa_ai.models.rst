sherpa\_ai.models package
=========================

Overview
--------

The ``models`` package provides interfaces and wrappers for language models in Sherpa AI, enabling seamless integration with various LLM providers while adding enhanced functionality like logging and error handling.

.. admonition:: Key Components
   :class: note
   
   * **SherpaBaseChatModel**: Core interface for chat-based language models
   * **SherpaBaseModel**: Base implementation for all model types
   * **ChatModelWithLogging**: Chat model wrapper with integrated logging capabilities

Example Usage
-------------

.. code-block:: python

   from sherpa_ai.models.sherpa_base_chat_model import SherpaBaseChatModel
   
   # Initialize a chat model
   model = SherpaBaseChatModel(
       model_name="gpt-4",
       temperature=0.7,
       max_tokens=1000
   )
   
   # Generate a response to a user query
   response = model.generate(
       messages=[
           {"role": "system", "content": "You are a helpful assistant."},
           {"role": "user", "content": "Explain quantum computing in simple terms."}
       ]
   )
   
   print(response)

Submodules
----------

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Module
     - Description
   * - :mod:`sherpa_ai.models.chat_model_with_logging`
     - Provides a chat model wrapper with integrated logging capabilities.
   * - :mod:`sherpa_ai.models.sherpa_base_chat_model`
     - Implements the core interface for chat-based language models.
   * - :mod:`sherpa_ai.models.sherpa_base_model`
     - Contains the base implementation for all model types in the system.

.. toctree::
   :hidden:

   sherpa_ai.models.chat_model_with_logging
   sherpa_ai.models.sherpa_base_chat_model
   sherpa_ai.models.sherpa_base_model

sherpa\_ai.models.chat\_model\_with\_logging module
---------------------------------------------------

.. automodule:: sherpa_ai.models.chat_model_with_logging
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.models.sherpa\_base\_chat\_model module
--------------------------------------------------

.. automodule:: sherpa_ai.models.sherpa_base_chat_model
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.models.sherpa\_base\_model module
--------------------------------------------

.. automodule:: sherpa_ai.models.sherpa_base_model
   :members:
   :undoc-members:
   :show-inheritance:

Module contents
---------------

.. automodule:: sherpa_ai.models
   :members:
   :undoc-members:
   :show-inheritance: