sherpa\_ai.database package
===========================

Overview
--------

The ``database`` package provides database interaction capabilities for Sherpa AI, enabling persistence, tracking, and analysis of agent interactions and user data.

.. admonition:: Key Components
   :class: note
   
   * **UserUsageTracker**: Tracks and records user interactions with Sherpa AI
   * **Storage Management**: Tools for storing and retrieving data
   * **Usage Analytics**: Capabilities for analyzing usage patterns

Example Usage
-------------

.. code-block:: python

   from sherpa_ai.database.user_usage_tracker import UserUsageTracker
   
   # Initialize a usage tracker
   tracker = UserUsageTracker(user_id="user123")
   
   # Record a user interaction
   tracker.track_interaction(
       query="What is machine learning?",
       response_length=1250,
       tokens_used=350,
       model_name="gpt-4"
   )
   
   # Get usage statistics
   monthly_stats = tracker.get_monthly_usage()
   print(f"Tokens used this month: {monthly_stats['total_tokens']}")

Submodules
----------

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Module
     - Description
   * - :mod:`sherpa_ai.database.user_usage_tracker`
     - Implements tracking and analytics for user interactions with the system.

.. toctree::
   :hidden:

   sherpa_ai.database.user_usage_tracker

sherpa\_ai.database.user\_usage\_tracker module
-----------------------------------------------

.. automodule:: sherpa_ai.database.user_usage_tracker
   :members:
   :undoc-members:
   :show-inheritance:

Module contents
---------------

.. automodule:: sherpa_ai.database
   :members:
   :undoc-members:
   :show-inheritance: