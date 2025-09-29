sherpa\_ai.output\_parsers package
==================================

Overview
--------

The ``output_parsers`` package provides tools for validating, formatting, and transforming model outputs in Sherpa AI. These parsers ensure that responses meet specific criteria and formats before being presented to users.

.. admonition:: Key Components
   :class: note
   
   * **Citation Validation**: Ensures proper citation formatting and accuracy
   * **Number Validation**: Verifies numerical responses for correctness
   * **Link Parsing**: Extracts and validates hyperlinks from responses
   * **Self-Consistency**: Implements self-consistency improvement for complex Pytandic outputs
   * **Format Conversion**: Converts between different formats (e.g., Markdown to Slack)

Example Usage
-------------

.. code-block:: python

   from sherpa_ai.output_parsers.citation_validation import CitationValidator
   from sherpa_ai.output_parsers.number_validation import NumberValidator
   
   # Validate citations in a response
   citation_validator = CitationValidator()
   citation_result = citation_validator.validate(
       "According to Smith et al. (2023), AI has made significant progress."
   )
   print(f"Citation valid: {citation_result.is_valid}")
   
   # Validate numerical answers
   number_validator = NumberValidator()
   number_result = number_validator.validate("The answer is 42.5 meters.")
   print(f"Extracted number: {number_result.validated_output}")

Submodules
----------

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Module
     - Description
   * - :mod:`sherpa_ai.output_parsers.base`
     - Provides abstract base classes for all output parsers.
   * - :mod:`sherpa_ai.output_parsers.citation_validation`
     - Implements validation for proper citation formatting and accuracy.
   * - :mod:`sherpa_ai.output_parsers.link_parse`
     - Contains tools for extracting and validating hyperlinks in responses.
   * - :mod:`sherpa_ai.output_parsers.md_to_slack_parse`
     - Provides conversion from Markdown to Slack message formatting.
   * - :mod:`sherpa_ai.output_parsers.number_validation`
     - Implements validation for numerical answers and calculations.
   * - :mod:`sherpa_ai.output_parsers.validation_result`
     - Contains the ValidationResult class for representing validation outcomes.
   * - :mod:`sherpa_ai.output_parsers.self_consistency`
     - Implements self-consistency improvement for complex Pydantic outputs.

.. toctree::
   :hidden:

   sherpa_ai.output_parsers.base
   sherpa_ai.output_parsers.citation_validation
   sherpa_ai.output_parsers.link_parse
   sherpa_ai.output_parsers.md_to_slack_parse
   sherpa_ai.output_parsers.number_validation
   sherpa_ai.output_parsers.validation_result
   sherpa_ai.output_parsers.self_consistency

sherpa\_ai.output\_parsers.base module
--------------------------------------

.. automodule:: sherpa_ai.output_parsers.base
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.output\_parsers.citation\_validation module
------------------------------------------------------

.. automodule:: sherpa_ai.output_parsers.citation_validation
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.output\_parsers.link\_parse module
---------------------------------------------

.. automodule:: sherpa_ai.output_parsers.link_parse
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.output\_parsers.md\_to\_slack\_parse module
------------------------------------------------------

.. automodule:: sherpa_ai.output_parsers.md_to_slack_parse
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.output\_parsers.number\_validation module
----------------------------------------------------

.. automodule:: sherpa_ai.output_parsers.number_validation
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.output\_parsers.validation\_result module
----------------------------------------------------

.. automodule:: sherpa_ai.output_parsers.validation_result
   :members:
   :undoc-members:
   :show-inheritance:


.. _self-consistency-module:

sherpa\_ai.output\_parsers.self\_consistency module
---------------------------------------------------

.. automodule:: sherpa_ai.output_parsers.self_consistency
   :members:
   :undoc-members:
   :show-inheritance:

Module contents
---------------

.. automodule:: sherpa_ai.output_parsers
   :members:
   :undoc-members:
   :show-inheritance: