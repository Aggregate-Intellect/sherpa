sherpa\_ai.test\_utils package
==========================

Overview
--------

The ``test_utils`` package provides testing utilities to streamline and standardize test development
for the Sherpa AI framework. It includes tools for managing test data files, working with both real
and mock language models, and configuring logging for test environments.

.. admonition:: Key Components
   :class: note
   
   * **Data Utilities**: Tools for locating and loading test data files
   * **LLM Mocking**: Utilities for creating fake LLMs with predetermined responses
   * **Logging Utilities**: Tools for configuring logging in test environments

Example Usage
-------------

.. code-block:: python

   import pytest
   from sherpa_ai.test_utils.data import get_test_data_file_path
   from sherpa_ai.test_utils.llms import get_llm
   from sherpa_ai.test_utils.loggers import config_logger_level
   
   # Test using data utilities
   def test_with_data_file(get_test_data_file_path):
       data_path = get_test_data_file_path(__file__, "test_data.json")
       # Use the data path in the test...
   
   # Test using fake LLMs
   @pytest.mark.parametrize("external_api", [False])
   def test_with_llm(get_llm):
       llm = get_llm(__file__, "test_agent_response")
       response = llm.invoke("What is AI?")
       assert "intelligence" in response.content.lower()
   
   # Test with custom logging
   def test_with_logging(config_logger_level):
       config_logger_level("DEBUG")
       # Test will now log at DEBUG level

Submodules
----------

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Module
     - Description
   * - :mod:`sherpa_ai.test_utils.data`
     - Utilities for locating and loading test data files relative to test files.
   * - :mod:`sherpa_ai.test_utils.llms`
     - Tools for creating both real and fake language models for testing.
   * - :mod:`sherpa_ai.test_utils.loggers`
     - Utilities for configuring and isolating logging in test environments.

.. toctree::
   :hidden:

   sherpa_ai.test_utils.data
   sherpa_ai.test_utils.llms
   sherpa_ai.test_utils.loggers

sherpa\_ai.test\_utils.data module
---------------------------------

.. automodule:: sherpa_ai.test_utils.data
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.test\_utils.llms module
---------------------------------

.. automodule:: sherpa_ai.test_utils.llms
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.test\_utils.loggers module
------------------------------------

.. automodule:: sherpa_ai.test_utils.loggers
   :members:
   :undoc-members:
   :show-inheritance:

Module contents
--------------

.. automodule:: sherpa_ai.test_utils
   :members:
   :undoc-members:
   :show-inheritance: 