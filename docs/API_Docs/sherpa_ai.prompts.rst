sherpa\_ai.prompts package
=======================

Overview
--------

The ``prompts`` package provides a comprehensive system for creating, loading, and formatting prompts
for language models. It supports both text-based and chat-based prompts, and includes features for
variable substitution, template rendering, and managing prompt collections.

.. admonition:: Key Components
   :class: note
   
   * **Base**: Core classes for representing different prompt types
   * **PromptLoader**: Utilities for loading and validating prompts from JSON files
   * **PromptTemplate**: Tools for formatting prompts with variable substitution

Example Usage
-------------

.. code-block:: python

   from sherpa_ai.prompts.prompt_template_loader import PromptTemplate
   
   # Initialize prompt template loader with a JSON file of prompts
   template = PromptTemplate("prompts.json")
   
   # Format a prompt with variable substitution
   formatted_prompt = template.format_prompt(
       "system", "greeting", "1.0",
       {"name": "Alice", "time": "morning"}
   )
   
   # Get a complete formatted prompt with metadata
   full_prompt = template.get_full_formatted_prompt(
       "agent", "task", "1.0",
       {"task_name": "analysis", "context": "financial data"}
   )
   
   print(formatted_prompt)
   print(full_prompt["description"])

Submodules
----------

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Module
     - Description
   * - :mod:`sherpa_ai.prompts.Base`
     - Core classes for representing different types of prompts (text and chat).
   * - :mod:`sherpa_ai.prompts.prompt_loader`
     - Utilities for loading, validating, and querying prompt definitions from JSON files.
   * - :mod:`sherpa_ai.prompts.prompt_template_loader`
     - Tools for formatting prompts with variable substitution and retrieving complete prompt packages.

.. toctree::
   :hidden:

   sherpa_ai.prompts.Base
   sherpa_ai.prompts.prompt_loader
   sherpa_ai.prompts.prompt_template_loader

sherpa\_ai.prompts.Base module
------------------------------

.. automodule:: sherpa_ai.prompts.Base
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.prompts.prompt\_loader module
---------------------------------------

.. automodule:: sherpa_ai.prompts.prompt_loader
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.prompts.prompt\_template\_loader module
------------------------------------------------

.. automodule:: sherpa_ai.prompts.prompt_template_loader
   :members:
   :undoc-members:
   :show-inheritance:

Module contents
--------------

.. automodule:: sherpa_ai.prompts
   :members:
   :undoc-members:
   :show-inheritance: 