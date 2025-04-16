sherpa\_ai.scrape package
======================

Overview
--------

The ``scrape`` package provides utilities for extracting and processing information from
external sources like files, websites, and repositories. These tools enable agents to
gather relevant information from structured and unstructured data sources.

.. admonition:: Key Components
   :class: note
   
   * **FileScaper**: Tools for extracting content from local files
   * **GitHubReadmeExtractor**: Utilities for retrieving README content from GitHub
   * **PromptReconstructor**: Tools for rebuilding prompts from extracted content

Example Usage
-------------

.. code-block:: python

   from sherpa_ai.scrape.file_scraper import FileScraper
   from sherpa_ai.scrape.extract_github_readme import GitHubReadmeExtractor
   
   # Extract content from local files
   scraper = FileScraper()
   content = scraper.scrape_file("path/to/document.txt")
   
   # Parse Python files for structured content
   python_content = scraper.scrape_python_file("path/to/script.py")
   print(f"Found {len(python_content['classes'])} classes")
   print(f"Found {len(python_content['functions'])} functions")
   
   # Extract README from a GitHub repository
   github_extractor = GitHubReadmeExtractor()
   readme = github_extractor.extract_readme("username", "repository")
   print(readme)

Submodules
----------

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Module
     - Description
   * - :mod:`sherpa_ai.scrape.extract_github_readme`
     - Utilities for retrieving and processing README files from GitHub repositories.
   * - :mod:`sherpa_ai.scrape.file_scraper`
     - Tools for extracting and parsing content from local files in various formats.
   * - :mod:`sherpa_ai.scrape.prompt_reconstructor`
     - Functionality for rebuilding and formatting prompts from extracted content.

.. toctree::
   :hidden:

   sherpa_ai.scrape.extract_github_readme
   sherpa_ai.scrape.file_scraper
   sherpa_ai.scrape.prompt_reconstructor

sherpa\_ai.scrape.extract\_github\_readme module
----------------------------------------------

.. automodule:: sherpa_ai.scrape.extract_github_readme
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.scrape.file\_scraper module
------------------------------------

.. automodule:: sherpa_ai.scrape.file_scraper
   :members:
   :undoc-members:
   :show-inheritance:

sherpa\_ai.scrape.prompt\_reconstructor module
--------------------------------------------

.. automodule:: sherpa_ai.scrape.prompt_reconstructor
   :members:
   :undoc-members:
   :show-inheritance:

Module contents
--------------

.. automodule:: sherpa_ai.scrape
   :members:
   :undoc-members:
   :show-inheritance: 