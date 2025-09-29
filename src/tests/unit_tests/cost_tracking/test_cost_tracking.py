"""Comprehensive tests for the cost tracking system."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from sherpa_ai.cost_tracking.pricing import PricingManager
from sherpa_ai.cost_tracking.logger import UsageLogger
from sherpa_ai.cost_tracking.reporting import CostReporter
from sherpa_ai.database.user_usage_tracker import UserUsageTracker


class TestPricingManager:
    """Test cases for PricingManager class."""

    def test_default_pricing_initialization(self):
        """Test that PricingManager initializes with default pricing."""
        pricing = PricingManager()
        
        # Check that default pricing is loaded
        assert len(pricing.pricing_data) > 0
        
        # Check some default models are present
        assert "gpt-4o" in pricing.pricing_data
        assert "gpt-4o-mini" in pricing.pricing_data
        assert "claude-3-5-sonnet-20241022" in pricing.pricing_data

    def test_calculate_cost_with_separate_tokens(self):
        """Test cost calculation with separate input/output tokens."""
        pricing = PricingManager()
        
        # Test known model with separate tokens
        cost = pricing.calculate_cost("gpt-4o", 1000, 500)
        assert cost > 0
        assert isinstance(cost, float)
        
        # Test with zero tokens
        cost_zero = pricing.calculate_cost("gpt-4o", 0, 0)
        assert cost_zero == 0.0

    def test_calculate_cost_from_usage_metadata(self):
        """Test cost calculation from usage metadata."""
        pricing = PricingManager()
        
        usage_metadata = {
            "input_tokens": 1000,
            "output_tokens": 500
        }
        
        cost = pricing.calculate_cost_from_usage_metadata("gpt-4o", usage_metadata)
        assert cost > 0
        assert isinstance(cost, float)

    def test_custom_pricing_file(self):
        """Test loading pricing from a custom JSON file."""
        custom_pricing = {
            "gpt-4o": {
                "input_price_per_1k": 0.005,
                "output_price_per_1k": 0.015
            },
            "custom-model": {
                "input_price_per_1k": 0.002,
                "output_price_per_1k": 0.008
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(custom_pricing, f)
            temp_file = f.name

        try:
            pricing = PricingManager(config_path=temp_file)
            
            # Check that custom pricing is loaded
            assert "gpt-4o" in pricing.pricing_data
            assert "custom-model" in pricing.pricing_data
            
            # Test cost calculation with custom pricing
            cost = pricing.calculate_cost("custom-model", 1000, 500)
            assert cost > 0
            
        finally:
            os.unlink(temp_file)

    def test_get_pricing(self):
        """Test getting pricing information."""
        pricing = PricingManager()
        
        # Test getting all pricing
        all_prices = pricing.get_pricing()
        assert isinstance(all_prices, dict)
        assert "gpt-4o" in all_prices

    def test_update_pricing(self):
        """Test updating pricing for existing models."""
        pricing = PricingManager()
        
        # Update existing model
        new_pricing = {
            "gpt-4o": {
                "input_price_per_1k": 0.010,
                "output_price_per_1k": 0.020
            }
        }
        pricing.update_pricing(new_pricing)
        
        # Check that pricing was updated
        assert pricing.pricing_data["gpt-4o"]["input_price_per_1k"] == 0.010
        assert pricing.pricing_data["gpt-4o"]["output_price_per_1k"] == 0.020

    def test_add_model(self):
        """Test adding pricing for new models."""
        pricing = PricingManager()
        
        # Add new model
        pricing.add_model("new-model", 0.005, 0.010)
        
        # Check that model was added
        assert "new-model" in pricing.pricing_data
        assert pricing.pricing_data["new-model"]["input_price_per_1k"] == 0.005
        assert pricing.pricing_data["new-model"]["output_price_per_1k"] == 0.010

    def test_unknown_model(self):
        """Test handling of unknown models."""
        pricing = PricingManager()
        
        # Test unknown model returns 0 cost
        cost = pricing.calculate_cost("unknown-model", 1000, 500)
        assert cost == 0.0

    def test_pricing_with_different_token_amounts(self):
        """Test pricing calculations with various token amounts."""
        pricing = PricingManager()
        
        test_cases = [
            ("gpt-4o", 100, 50, 0.001),
            ("gpt-4o", 1000, 500, 0.01),
            ("gpt-4o-mini", 1000, 500, 0.000375),
        ]
        
        for model, input_tokens, output_tokens, expected_cost in test_cases:
            cost = pricing.calculate_cost(model, input_tokens, output_tokens)
            assert cost > 0
            assert isinstance(cost, float)

    def test_pricing_with_zero_tokens(self):
        """Test pricing calculation with zero tokens."""
        pricing = PricingManager()
        
        cost = pricing.calculate_cost("gpt-4o", 0, 0)
        assert cost == 0.0

    def test_invalid_json_file(self):
        """Test handling of invalid JSON files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_file = f.name

        try:
            # Should have empty pricing data when JSON is invalid
            pricing = PricingManager(config_path=temp_file)
            assert len(pricing.pricing_data) == 0  # Should have empty pricing data
            
        finally:
            os.unlink(temp_file)

    def test_nonexistent_file(self):
        """Test handling of non-existent files."""
        # Should fall back to default pricing
        pricing = PricingManager(config_path="nonexistent_file.json")
        assert len(pricing.pricing_data) > 0  # Should have default pricing


class TestCostThresholdAlerts:
    """Test cost threshold alert functionality."""

    def test_80_percent_alert(self):
        """Test that 80% threshold alert is triggered."""
        alert_callback = Mock()
        logger = UsageLogger(
            daily_cost_limit=10.0,
            alert_threshold=0.8,
            alert_callback=alert_callback
        )
        
        # Add usage to reach 80% of limit ($8.00)
        logger.log_usage("user1", 8.0, "gpt-4o")
        
        # Check that alert was triggered
        alert_callback.assert_called_once()
        call_args = alert_callback.call_args
        assert call_args[1]["user_id"] == "user1"
        assert call_args[1]["total_cost"] == 8.0
        assert call_args[1]["cost_percentage"] == 80.0
        assert call_args[1]["alert_level"] == "WARNING"
        assert call_args[1]["threshold"] == 80

    def test_100_percent_alert(self):
        """Test that 100% threshold alert is triggered."""
        alert_callback = Mock()
        logger = UsageLogger(
            daily_cost_limit=10.0,
            alert_threshold=0.8,
            alert_callback=alert_callback
        )
        
        # Add usage to reach 100% of limit ($10.00)
        logger.log_usage("user1", 10.0, "gpt-4o")
        
        # Check that both 80% and 100% alerts were triggered
        assert alert_callback.call_count == 2
        
        # Check 100% alert specifically
        calls = alert_callback.call_args_list
        critical_alert = next(call for call in calls if call[1]["alert_level"] == "CRITICAL")
        assert critical_alert[1]["user_id"] == "user1"
        assert critical_alert[1]["total_cost"] == 10.0
        assert critical_alert[1]["cost_percentage"] == 100.0
        assert critical_alert[1]["threshold"] == 100

    def test_no_duplicate_alerts(self):
        """Test that alerts are not sent multiple times for the same threshold."""
        alert_callback = Mock()
        logger = UsageLogger(
            daily_cost_limit=10.0,
            alert_threshold=0.8,
            alert_callback=alert_callback
        )
        
        # Add usage to reach 80% of limit
        logger.log_usage("user1", 8.0, "gpt-4o")
        
        # Add more usage (should not trigger another 80% alert)
        logger.log_usage("user1", 1.0, "gpt-4o")
        
        # Should only have one 80% alert
        warning_alerts = [call for call in alert_callback.call_args_list if call[1]["alert_level"] == "WARNING"]
        assert len(warning_alerts) == 1

    def test_multiple_users_separate_alerts(self):
        """Test that alerts work independently for different users."""
        alert_callback = Mock()
        logger = UsageLogger(
            daily_cost_limit=10.0,
            alert_threshold=0.8,
            alert_callback=alert_callback
        )
        
        # User 1 reaches 80%
        logger.log_usage("user1", 8.0, "gpt-4o")
        
        # User 2 reaches 80%
        logger.log_usage("user2", 8.0, "gpt-4o")
        
        # Should have 2 alerts (one for each user)
        assert alert_callback.call_count == 2

    def test_reset_user_cost(self):
        """Test that user cost tracking can be reset."""
        alert_callback = Mock()
        logger = UsageLogger(
            daily_cost_limit=10.0,
            alert_threshold=0.8,
            alert_callback=alert_callback
        )
        
        # User reaches 80%
        logger.log_usage("user1", 8.0, "gpt-4o")
        assert alert_callback.call_count == 1
        
        # Reset user cost
        logger.reset_user_cost("user1")
        
        # User reaches 80% again (should trigger new alert)
        logger.log_usage("user1", 8.0, "gpt-4o")
        assert alert_callback.call_count == 2

    def test_get_user_cost(self):
        """Test getting current cost for a user."""
        logger = UsageLogger(daily_cost_limit=10.0)
        
        # Initially no cost
        assert logger.get_user_cost("user1") == 0.0
        
        # Add some cost
        logger.log_usage("user1", 5.0, "gpt-4o")
        assert logger.get_user_cost("user1") == 5.0
        
        # Add more cost
        logger.log_usage("user1", 3.0, "gpt-4o")
        assert logger.get_user_cost("user1") == 8.0

    def test_reset_all_costs(self):
        """Test resetting all user costs."""
        alert_callback = Mock()
        logger = UsageLogger(
            daily_cost_limit=10.0,
            alert_threshold=0.8,
            alert_callback=alert_callback
        )
        
        # Multiple users reach 80%
        logger.log_usage("user1", 8.0, "gpt-4o")
        logger.log_usage("user2", 8.0, "gpt-4o")
        assert alert_callback.call_count == 2
        
        # Reset all costs
        logger.reset_all_costs()
        
        # Users reach 80% again (should trigger new alerts)
        logger.log_usage("user1", 8.0, "gpt-4o")
        logger.log_usage("user2", 8.0, "gpt-4o")
        assert alert_callback.call_count == 4

    def test_alert_without_callback(self):
        """Test that alerts work even without custom callback."""
        logger = UsageLogger(daily_cost_limit=10.0)
        
        # Should not raise exception
        logger.log_usage("user1", 8.0, "gpt-4o")
        assert logger.get_user_cost("user1") == 8.0

    def test_alert_callback_error_handling(self):
        """Test that alert callback errors are handled gracefully."""
        def failing_callback(**kwargs):
            raise Exception("Callback error")
        
        logger = UsageLogger(
            daily_cost_limit=10.0,
            alert_callback=failing_callback
        )
        
        # Should not raise exception even if callback fails
        logger.log_usage("user1", 8.0, "gpt-4o")
        assert logger.get_user_cost("user1") == 8.0

    def test_custom_alert_message_format(self):
        """Test that alert messages have correct format."""
        with patch('sherpa_ai.cost_tracking.logger.logger') as mock_logger:
            logger = UsageLogger(daily_cost_limit=10.0)
            
            # Trigger 80% alert
            logger.log_usage("user1", 8.0, "gpt-4o")
            
            # Check that warning was logged
            mock_logger.warning.assert_called()
            warning_call = mock_logger.warning.call_args[0][0]
            assert "🚨 WARNING ALERT" in warning_call
            assert "User user1 has reached 80.0%" in warning_call
            assert "$8.00/$10.00" in warning_call


class TestCostTrackingIntegration:
    """Integration tests for the complete cost tracking system."""

    def test_pricing_and_alerts_integration(self):
        """Test that pricing and alerts work together."""
        # Create pricing manager
        pricing = PricingManager()
        
        # Create alert callback
        alert_callback = Mock()
        
        # Create usage logger with alerts
        logger = UsageLogger(
            daily_cost_limit=10.0,
            alert_callback=alert_callback
        )
        
        # Calculate cost using pricing manager
        cost = pricing.calculate_cost("gpt-4o", 1000, 500)
        assert cost > 0
        
        # Log usage with calculated cost
        logger.log_usage("user1", cost, "gpt-4o")
        
        # Check that cost tracking works
        assert logger.get_user_cost("user1") == cost

    def test_usage_metadata_integration(self):
        """Test integration with usage metadata."""
        pricing = PricingManager()
        logger = UsageLogger(daily_cost_limit=10.0)
        
        # Simulate usage metadata from LangChain
        usage_metadata = {
            "input_tokens": 1000,
            "output_tokens": 500,
            "total_tokens": 1500
        }
        
        # Calculate cost from metadata
        cost = pricing.calculate_cost_from_usage_metadata("gpt-4o", usage_metadata)
        
        # Log usage with metadata
        logger.log_usage("user1", cost, "gpt-4o", usage_metadata=usage_metadata)
        
        # Verify cost tracking
        assert logger.get_user_cost("user1") == cost

    def test_multiple_models_cost_tracking(self):
        """Test cost tracking across multiple models."""
        pricing = PricingManager()
        logger = UsageLogger(daily_cost_limit=20.0)
        
        # Test different models
        models = ["gpt-4o", "gpt-4o-mini", "claude-3-5-sonnet-20241022"]
        total_cost = 0.0
        
        for model in models:
            cost = pricing.calculate_cost(model, 100, 50)
            logger.log_usage("user1", cost, model)
            total_cost += cost
        
        # Verify total cost tracking
        assert abs(logger.get_user_cost("user1") - total_cost) < 0.001

    def test_cost_threshold_with_real_pricing(self):
        """Test cost thresholds with actual pricing calculations."""
        pricing = PricingManager()
        alert_callback = Mock()
        
        logger = UsageLogger(
            daily_cost_limit=1.0,  # $1 daily limit
            alert_callback=alert_callback
        )
        
        # Calculate realistic usage that should trigger alerts
        # GPT-4o: $0.005 input, $0.015 output per 1k tokens
        # To reach $0.80 (80% of $1.00), need: 100,000 input + 20,000 output tokens
        input_tokens = 100000
        output_tokens = 20000
        
        cost = pricing.calculate_cost("gpt-4o", input_tokens, output_tokens)
        logger.log_usage("user1", cost, "gpt-4o")
        
        # Should trigger 80% alert
        assert alert_callback.call_count == 1
        call_args = alert_callback.call_args[1]
        assert call_args["alert_level"] == "WARNING"
        assert call_args["cost_percentage"] >= 80.0


class TestCostReporter:
    """Test cases for CostReporter class."""
    
    def _create_isolated_tracker(self):
        """Create an isolated tracker with temporary database."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            temp_db = f.name
        return UserUsageTracker(db_name=temp_db, db_url=f"sqlite:///{temp_db}"), temp_db

    def test_get_tokens_from_usage_metadata(self):
        """Test extracting token counts from usage metadata."""
        reporter = CostReporter()
        
        usage_metadata = {
            "input_tokens": 1000,
            "output_tokens": 500,
            "total_tokens": 1500
        }
        
        tokens = reporter.get_tokens_from_usage_metadata(usage_metadata)
        assert tokens["input_tokens"] == 1000
        assert tokens["output_tokens"] == 500
        assert tokens["total_tokens"] == 1500

    def test_get_token_details_from_usage_metadata(self):
        """Test extracting detailed token information."""
        reporter = CostReporter()
        
        usage_metadata = {
            "input_token_details": {
                "cache_creation": 100,
                "cache_read": 50,
                "audio": 25
            },
            "output_token_details": {
                "reasoning": 200,
                "audio": 10
            }
        }
        
        details = reporter.get_token_details_from_usage_metadata(usage_metadata)
        assert details["reasoning_tokens"] == 200
        assert details["cache_creation"] == 100
        assert details["cache_read"] == 50
        assert details["audio_tokens"] == 35  # 25 + 10

    def test_get_usage_metadata_statistics_empty(self):
        """Test usage statistics with no data."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            temp_db = f.name
        
        try:
            tracker = UserUsageTracker(db_name=temp_db, db_url=f"sqlite:///{temp_db}")
            reporter = CostReporter(tracker)
            
            stats = reporter.get_usage_metadata_statistics()
            assert stats["total_records"] == 0
            assert stats["total_cost"] == 0.0
            assert stats["total_tokens"] == 0
            assert stats["model_breakdown"] == {}
            assert stats["token_details"] == {}
        finally:
            os.unlink(temp_db)

    def test_get_usage_metadata_statistics_with_data(self):
        """Test usage statistics with sample data."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            temp_db = f.name
        
        try:
            tracker = UserUsageTracker(db_name=temp_db, db_url=f"sqlite:///{temp_db}")
            reporter = CostReporter(tracker)
            
            # Add some usage data
            tracker.add_usage("user1", input_tokens=1000, output_tokens=500, model_name="gpt-4o")
            
            stats = reporter.get_usage_metadata_statistics()
            assert stats["total_records"] == 1
            assert stats["total_cost"] > 0
            assert "gpt-4o" in stats["model_breakdown"]
        finally:
            os.unlink(temp_db)

    def test_get_top_users_by_cost(self):
        """Test getting top users by cost."""
        tracker, temp_db = self._create_isolated_tracker()
        reporter = CostReporter(tracker)
        
        try:
            # Add usage for multiple users
            tracker.add_usage("user1", input_tokens=1000, output_tokens=500, model_name="gpt-4o")
            tracker.add_usage("user2", input_tokens=2000, output_tokens=1000, model_name="gpt-4o")
            tracker.add_usage("user1", input_tokens=500, output_tokens=250, model_name="gpt-4o-mini")
            
            top_users = reporter.get_top_users_by_cost(limit=2)
            assert len(top_users) == 2
            assert top_users[0]["user_id"] == "user2"  # Higher cost
            assert top_users[1]["user_id"] == "user1"
            assert all("total_cost" in user for user in top_users)
            assert all("total_tokens" in user for user in top_users)
            assert all("total_calls" in user for user in top_users)
        finally:
            os.unlink(temp_db)

    def test_get_top_agents_by_cost(self):
        """Test getting top agents by cost."""
        tracker, temp_db = self._create_isolated_tracker()
        reporter = CostReporter(tracker)
        
        try:
            # Add usage for multiple agents
            tracker.add_usage("user1", input_tokens=1000, output_tokens=500, model_name="gpt-4o", agent_name="agent1")
            tracker.add_usage("user2", input_tokens=2000, output_tokens=1000, model_name="gpt-4o", agent_name="agent2")
            tracker.add_usage("user1", input_tokens=500, output_tokens=250, model_name="gpt-4o-mini", agent_name="agent1")
            
            top_agents = reporter.get_top_agents_by_cost(limit=2)
            assert len(top_agents) == 2
            # agent2 has higher cost (2000+1000 tokens vs 1000+500+500+250 tokens)
            assert top_agents[0]["agent_name"] == "agent2"  # Higher total cost
            assert top_agents[1]["agent_name"] == "agent1"
            assert all("total_cost" in agent for agent in top_agents)
            assert all("total_tokens" in agent for agent in top_agents)
            assert all("total_calls" in agent for agent in top_agents)
        finally:
            os.unlink(temp_db)

    def test_get_model_statistics(self):
        """Test getting model usage statistics."""
        tracker, temp_db = self._create_isolated_tracker()
        reporter = CostReporter(tracker)
        
        try:
            # Add usage for multiple models
            tracker.add_usage("user1", input_tokens=1000, output_tokens=500, model_name="gpt-4o")
            tracker.add_usage("user2", input_tokens=2000, output_tokens=1000, model_name="gpt-4o-mini")
            tracker.add_usage("user1", input_tokens=500, output_tokens=250, model_name="gpt-4o")
            
            model_stats = reporter.get_model_statistics()
            assert "gpt-4o" in model_stats
            assert "gpt-4o-mini" in model_stats
            assert model_stats["gpt-4o"]["total_calls"] == 2
            assert model_stats["gpt-4o-mini"]["total_calls"] == 1
            assert all("total_cost" in stats for stats in model_stats.values())
            assert all("total_tokens" in stats for stats in model_stats.values())
        finally:
            os.unlink(temp_db)

    def test_export_data_json(self):
        """Test exporting data to JSON format."""
        tracker, temp_db = self._create_isolated_tracker()
        reporter = CostReporter(tracker)
        
        try:
            # Add some data
            tracker.add_usage("user1", input_tokens=1000, output_tokens=500, model_name="gpt-4o")
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                temp_file = f.name
            
            try:
                success = reporter.export_data(temp_file, format="json")
                assert success
                
                # Check that file was created and has content
                with open(temp_file, 'r') as f:
                    data = json.load(f)
                assert len(data) > 0
            finally:
                os.unlink(temp_file)
        finally:
            os.unlink(temp_db)

    def test_export_data_csv(self):
        """Test exporting data to CSV format."""
        tracker, temp_db = self._create_isolated_tracker()
        reporter = CostReporter(tracker)
        
        try:
            # Add some data
            tracker.add_usage("user1", input_tokens=1000, output_tokens=500, model_name="gpt-4o")
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                temp_file = f.name
            
            try:
                success = reporter.export_data(temp_file, format="csv")
                assert success
                
                # Check that file was created and has content
                with open(temp_file, 'r') as f:
                    content = f.read()
                assert len(content) > 0
                assert "user_id" in content  # Should have CSV headers
            finally:
                os.unlink(temp_file)
        finally:
            os.unlink(temp_db)

    def test_export_data_invalid_format(self):
        """Test exporting data with invalid format."""
        tracker = UserUsageTracker()
        reporter = CostReporter(tracker)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            temp_file = f.name
        
        try:
            success = reporter.export_data(temp_file, format="invalid")
            assert not success
        finally:
            os.unlink(temp_file)

    def test_user_specific_statistics(self):
        """Test getting statistics for a specific user."""
        tracker, temp_db = self._create_isolated_tracker()
        reporter = CostReporter(tracker)
        
        try:
            # Add data for multiple users
            tracker.add_usage("user1", input_tokens=1000, output_tokens=500, model_name="gpt-4o")
            tracker.add_usage("user2", input_tokens=2000, output_tokens=1000, model_name="gpt-4o")
            
            # Get stats for user1 only
            user1_stats = reporter.get_usage_metadata_statistics(user_id="user1")
            all_stats = reporter.get_usage_metadata_statistics()
            
            assert user1_stats["total_records"] == 1
            assert all_stats["total_records"] == 2
            assert user1_stats["total_cost"] < all_stats["total_cost"]
        finally:
            os.unlink(temp_db)

    def test_usage_metadata_with_missing_fields(self):
        """Test handling of usage metadata with missing fields."""
        reporter = CostReporter()
        
        # Test with minimal metadata
        minimal_metadata = {"input_tokens": 100}
        tokens = reporter.get_tokens_from_usage_metadata(minimal_metadata)
        assert tokens["input_tokens"] == 100
        assert tokens["output_tokens"] == 0
        assert tokens["total_tokens"] == 0
        
        # Test with missing token details
        no_details_metadata = {"input_tokens": 100, "output_tokens": 50}
        details = reporter.get_token_details_from_usage_metadata(no_details_metadata)
        assert details["reasoning_tokens"] == 0
        assert details["cache_creation"] == 0
        assert details["cache_read"] == 0
        assert details["audio_tokens"] == 0
