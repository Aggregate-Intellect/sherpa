Cost Tracking with Sherpa
=========================

In this tutorial, we will explore Sherpa's cost tracking system that allows you to monitor and manage LLM usage costs across your applications. The system provides real-time monitoring, detailed reporting, and cost threshold alerts.

Overview
--------

Sherpa's cost tracking system consists of key components:

1. **PricingManager**: Manages model pricing and calculates costs
2. **UserUsageTracker**: Tracks usage per user, session, and agent
3. **UsageLogger**: Logs usage with cost threshold monitoring
4. **CLI Tools**: Command-line interface for cost analysis

Pricing Configuration
---------------------

Before using cost tracking, you need to configure model pricing. Sherpa comes with a default pricing configuration file that you can customize:

.. code:: json

   {
     "gpt-4o": {
       "input_price_per_1k": 0.005,
       "output_price_per_1k": 0.015
     },
     "gpt-4o-mini": {
       "input_price_per_1k": 0.00015,
       "output_price_per_1k": 0.0006
     },
     "claude-3-5-sonnet-20241022": {
       "input_price_per_1k": 0.003,
       "output_price_per_1k": 0.015
     }
   }

You can customize this file to match your specific model pricing or add new models. The pricing is specified per 1,000 tokens for both input and output tokens.

Database Configuration
-----------------------

Sherpa supports multiple database backends for cost tracking:

.. code:: python

    from sherpa_ai.database.user_usage_tracker import UserUsageTracker
    
    # Local SQLite (default)
    tracker = UserUsageTracker()
    
    # S3 storage
    tracker = UserUsageTracker(
        bucket_name="your-bucket",
        s3_file_key="cost_data/usage.json",
        log_to_s3=True
    )
    
    # Custom database (PostgreSQL, MySQL, etc.)
    tracker = UserUsageTracker(
        db_url="postgresql://user:password@localhost/cost_tracking"
    )

Configure via environment variables:

.. code:: bash

   export DB_URL="sqlite:///token_counter.db"
   export USAGE_LOG_TO_S3=true
   export AWS_ACCESS_KEY_ID="your_access_key"

Basic Usage
-----------

Setting Up Cost Tracking
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from sherpa_ai.database.user_usage_tracker import UserUsageTracker
    from sherpa_ai.cost_tracking.pricing import PricingManager

    # Initialize cost tracking
    pricing_manager = PricingManager("pricing_config.json")
    tracker = UserUsageTracker(pricing_manager=pricing_manager)

Tracking Usage
~~~~~~~~~~~~~~

Track usage for model calls:

.. code-block:: python

    # Track a simple model call
    tracker.add_usage(
        user_id="user_123",
        input_tokens=1000,
        output_tokens=500,
        model_name="gpt-4o",
        session_id="session_456",
        agent_name="qa_agent"
    )

    # Track with detailed metadata
    usage_metadata = {
        "input_tokens": 1500,
        "output_tokens": 800,
        "total_tokens": 2300
    }
    
    tracker.add_usage(
        user_id="user_123",
        usage_metadata=usage_metadata,
        model_name="gpt-4o"
    )

Cost Calculation
~~~~~~~~~~~~~~~~

Calculate costs for different models:

.. code-block:: python

    # Calculate cost for a model call
    cost = pricing_manager.calculate_cost("gpt-4o", 1000, 500)
    print(f"Cost: ${cost:.4f}")

    # Get pricing information
    pricing_data = pricing_manager.get_pricing()
    for model, prices in pricing_data.items():
        print(f"{model}: ${prices['input_price_per_1k']:.4f} input, ${prices['output_price_per_1k']:.4f} output per 1k tokens")

Advanced Features
-----------------

Cost Threshold Monitoring
~~~~~~~~~~~~~~~~~~~~~~~~~

Set up automatic cost monitoring with alerts:

.. code-block:: python

    from sherpa_ai.cost_tracking.logger import UsageLogger

    def cost_alert_callback(
        user_id: str,
        total_cost: float,
        cost_percentage: float,
        alert_level: str,
        threshold: int,
        daily_limit: float,
    ):
        print(
            f"{alert_level}: {user_id} has reached {cost_percentage:.1f}% "
            f"of the ${daily_limit:.2f} daily limit (${total_cost:.2f}; {threshold}% threshold)"
        )

    # The current logger checks at 80% and 100% of the daily limit.
    # Enable cost tracking in the environment to activate these checks.
    logger = UsageLogger(
        log_to_file=False,
        daily_cost_limit=10.0,
        alert_callback=cost_alert_callback
    )

    # Feed a synthetic record to demonstrate the callback; this makes no model call.
    logger.log_usage(
        user_id="example-user",
        cost=8.50,
        model_name="example-model",
        usage_metadata={
            "input_tokens": 1000,
            "output_tokens": 500,
            "total_tokens": 1500,
        },
    )

Cost Reporting
~~~~~~~~~~~~~~

Generate cost reports:

.. code-block:: python

    from sherpa_ai.cost_tracking.reporting import CostReporter

    # Get cost summary
    summary = tracker.get_cost_summary("user_123")
    print(f"Total cost: ${summary['total_cost']:.2f}")
    print(f"Model breakdown: {summary['model_breakdown']}")

    # Get top users by cost
    reporter = CostReporter(tracker=tracker)
    top_users = reporter.get_top_users_by_cost(limit=5)
    for user_data in top_users:
        print(f"User {user_data['user_id']}: ${user_data['total_cost']:.2f}")

CLI Usage
---------

Sherpa provides CLI tools for cost management:

.. code:: bash

   # Show cost summary
   python -m sherpa_ai.cost_tracking.cli summary

   # Show top users by cost
   python -m sherpa_ai.cost_tracking.cli top-users --limit 10

   # Estimate cost for a model call
   python -m sherpa_ai.cost_tracking.cli estimate --model gpt-4o --input-tokens 1000 --output-tokens 500

   # Export cost data
   python -m sherpa_ai.cost_tracking.cli export --output costs.json --format json

Configuration
-------------

Set up cost tracking through environment variables:

.. code:: bash

   # Enable cost tracking
   export ENABLE_COST_TRACKING=true
   export DAILY_COST_LIMIT=10.0
   export COST_ALERT_THRESHOLD=0.8
   export USAGE_LOG_TO_FILE=true

