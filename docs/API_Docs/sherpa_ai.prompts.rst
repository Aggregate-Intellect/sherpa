sherpa\_ai.prompts package
=======================

Overview
--------

The ``prompts`` package provides a comprehensive system for creating, loading, and formatting prompts
for language models. It supports text-based, chat-based, and JSON-structured prompts with features for
variable substitution, template rendering, validation, and managing prompt collections organized into groups.

.. admonition:: Key Components
   :class: note
   
   * **Base**: Core classes for representing different prompt types and organizing them into groups
   * **PromptLoader**: Utilities for loading, validating, and querying prompts from JSON files
   * **PromptTemplate**: Tools for formatting prompts with variable substitution and metadata retrieval

JSON Structure Requirements
---------------------------

Prompts must be organized in JSON files following this hierarchical structure:

**Root Structure** - Array of prompt groups:

.. code-block:: json

   [
     {
       "prompt_parent_id": "group_name",
       "description": "Description of the prompt group",
       "prompts": [...]
     }
   ]

**Prompt Structure** - Each prompt contains metadata and versions:

.. code-block:: json

   {
     "prompt_id": "unique_prompt_identifier",
     "description": "What this prompt does",
     "versions": [...]
   }

**Version Structure** - Each version defines the actual prompt content:

.. code-block:: json

   {
     "version": "1.0",
     "change_log": "Description of changes in this version",
     "type": "text|chat|json",
     "content": "varies by type",
     "variables": {"var_name": "default_value"},
     "response_format": {
       "type": "json_schema",
       "json_schema": {...}
     }
   }

**Content Types:**

* **Text prompts**: ``"content": "Simple text with {variables}"``
* **Chat prompts**: ``"content": [{"role": "system|user|assistant", "content": "message"}]``
* **JSON prompts**: ``"content": {"structured": "data with {variables}"}``

**Variable Substitution:**
Variables are defined with curly braces ``{variable_name}`` and can be replaced during formatting.

Complete Example
----------------

.. code-block:: json

   [
     {
       "prompt_parent_id": "math_operations",
       "description": "Prompts for mathematical calculations",
       "prompts": [
         {
           "prompt_id": "add_numbers",
           "description": "Prompt to add two numbers with structured output",
           "versions": [
             {
               "version": "1.0",
               "change_log": "Initial version",
               "type": "text",
               "content": "Add {first_num} and {second_num}",
               "variables": {
                 "first_num": 5,
                 "second_num": 10
               },
               "response_format": {
                 "type": "json_schema",
                 "json_schema": {
                   "name": "addition_result",
                   "schema": {
                     "type": "object",
                     "properties": {
                       "result": {"type": "number"},
                       "explanation": {"type": "string"}
                     },
                     "required": ["result", "explanation"]
                   }
                 }
               }
             }
           ]
         }
       ]
     }
   ]

Usage Examples
--------------

**Basic Prompt Loading and Formatting:**

.. code-block:: python

   from sherpa_ai.prompts.prompt_template_loader import PromptTemplate
   
   # Initialize with JSON file
   template = PromptTemplate("prompts.json")
   
   # Format a text prompt with custom variables
   formatted = template.format_prompt(
       prompt_parent_id="math_operations",
       prompt_id="add_numbers", 
       version="1.0",
       variables={"first_num": 15, "second_num": 25}
   )
   print(formatted)  # "Add 15 and 25"

**Working with Chat Prompts:**

.. code-block:: python

   # Format a chat prompt (returns list of message dicts)
   chat_prompt = template.format_prompt(
       prompt_parent_id="conversation",
       prompt_id="greeting_chat",
       version="1.0",
       variables={"name": "Alice"}
   )
   # Returns: [{"role": "system", "content": "..."}, {"role": "user", "content": "Hello Alice"}]

**Getting Complete Prompt Information:**

.. code-block:: python

   # Get formatted prompt with metadata and output schema
   full_prompt = template.get_full_formatted_prompt(
       prompt_parent_id="math_operations",
       prompt_id="add_numbers",
       version="1.0",
       variables={"first_num": 100, "second_num": 200}
   )
   
   print(full_prompt["description"])     # Prompt description
   print(full_prompt["content"])         # Formatted content
   print(full_prompt["output_schema"])   # Expected response format

**Direct Access Methods:**

.. code-block:: python

   from sherpa_ai.prompts.prompt_loader import PromptLoader
   
   loader = PromptLoader("prompts.json")
   
   # Get specific prompt version object
   version_obj = loader.get_prompt_version("math_operations", "add_numbers", "1.0")
   
   # Get just the content
   content = loader.get_prompt_content("math_operations", "add_numbers", "1.0")
   
   # Get output schema for response validation
   schema = loader.get_prompt_output_schema("math_operations", "add_numbers", "1.0")

Error Handling
--------------

The system includes robust validation and error handling:

.. code-block:: python

   from sherpa_ai.prompts.prompt_loader import InvalidPromptContentError
   
   try:
       loader = PromptLoader("invalid_prompts.json")
   except InvalidPromptContentError as e:
       print(f"Prompt validation failed: {e}")
   except FileNotFoundError as e:
       print(f"Prompt file not found: {e}")

Key Features
------------

* **Hierarchical Organization**: Prompts are organized into groups for better management
* **Version Control**: Multiple versions of prompts with change logs
* **Type Safety**: Validation ensures prompt structure matches declared types
* **Variable Substitution**: Dynamic content replacement with default values
* **Multiple Content Types**: Support for text, chat, and JSON-structured prompts
* **Response Schema**: Define expected output formats for structured responses
* **Resource Loading**: Automatic detection of package resources vs. filesystem paths

Submodules
----------

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Module
     - Description
   * - :mod:`sherpa_ai.prompts.Base`
     - Core Pydantic models for prompt types, versions, and groups with validation
   * - :mod:`sherpa_ai.prompts.prompt_loader`
     - Loading, validation, and querying of prompt definitions from JSON files
   * - :mod:`sherpa_ai.prompts.prompt_template_loader`
     - Template formatting with variable substitution and complete prompt retrieval

.. toctree::
   :hidden:

   sherpa_ai.prompts.Base
   sherpa_ai.prompts.prompt_loader
   sherpa_ai.prompts.prompt_template_loader

sherpa\_ai.prompts.Base module
------------------------------

This module defines the core data structures for the prompt system using Pydantic models for validation.

**Core Classes:**

* ``PromptVersion``: Base class for all prompt versions with common attributes
* ``TextPromptVersion``: Specialized for simple text-based prompts  
* ``ChatPromptVersion``: Specialized for conversation-style prompts with role/content pairs
* ``JsonPromptVersion``: Specialized for structured JSON prompts
* ``Prompt``: Container for prompt metadata and its versions
* ``PromptGroup``: Organizes related prompts under a common identifier

.. automodule:: sherpa_ai.prompts.Base
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.prompts.prompt\_loader module
---------------------------------------

This module handles loading prompts from JSON files and provides access methods for retrieving specific prompts and their components.

**Key Classes:**

* ``PromptLoader``: Main class for loading and validating prompt collections
* ``JsonToObject``: Utility for converting JSON data to Python objects
* ``InvalidPromptContentError``: Exception for validation failures

**Key Functions:**

* ``load_json()``: Loads JSON from package resources or filesystem
* ``get_prompts()``: Extracts prompt data from loaded JSON

.. automodule:: sherpa_ai.prompts.prompt_loader
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.prompts.prompt\_template\_loader module
------------------------------------------------

This module extends the base loader to provide template formatting capabilities with variable substitution.

**Key Class:**

* ``PromptTemplate``: Extends PromptLoader with formatting methods for variable substitution across all prompt types

**Key Methods:**

* ``format_prompt()``: Formats prompts by replacing variables with provided values
* ``get_full_formatted_prompt()``: Returns formatted content along with metadata and output schema

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