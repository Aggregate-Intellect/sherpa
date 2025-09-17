"""Tests for the configurable pricing system."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from sherpa_ai.cost_tracking.pricing import PricingManager, get_pricing_manager


class TestPricingManager:
    """Test cases for PricingManager class."""

    def test_default_pricing_initialization(self):
        """Test that PricingManager initializes with default pricing."""
        pricing = PricingManager()
        
        # Check that default pricing is loaded
        assert pricing.config_source == "default"
        assert len(pricing.pricing_data) > 0
        
        # Check some default models are present
        assert "gpt-4o" in pricing.pricing_data
        assert "gpt-4o-mini" in pricing.pricing_data
        assert "claude-3-5-sonnet-20241022" in pricing.pricing_data

    def test_calculate_cost_with_default_pricing(self):
        """Test cost calculation with default pricing."""
        pricing = PricingManager()
        
        # Test known model
        cost = pricing.calculate_cost("gpt-4o", 1000)
        assert cost == 0.01  # Default pricing for gpt-4o
        
        # Test unknown model (should use default)
        cost = pricing.calculate_cost("unknown-model", 1000)
        assert cost == 0.002  # Default fallback pricing
        
        # Test case insensitivity
        cost_lower = pricing.calculate_cost("gpt-4o", 1000)
        cost_upper = pricing.calculate_cost("GPT-4O", 1000)
        assert cost_lower == cost_upper

    def test_custom_pricing_file(self):
        """Test loading pricing from a custom JSON file."""
        custom_pricing = {
            "gpt-4o": 0.012,
            "gpt-4o-mini": 0.0004,
            "custom-model": 0.005
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(custom_pricing, f)
            temp_file = f.name
        
        try:
            pricing = PricingManager(config_path=temp_file)
            
            # Check config source
            assert pricing.config_source == f"file: {temp_file}"
            
            # Check custom pricing is loaded
            assert pricing.pricing_data["gpt-4o"] == 0.012
            assert pricing.pricing_data["gpt-4o-mini"] == 0.0004
            assert pricing.pricing_data["custom-model"] == 0.005
            
            # Test cost calculation with custom pricing
            cost = pricing.calculate_cost("gpt-4o", 1000)
            assert cost == 0.012
            
            cost = pricing.calculate_cost("custom-model", 1000)
            assert cost == 0.005
            
        finally:
            Path(temp_file).unlink()

    def test_environment_variable_pricing_json(self):
        """Test loading pricing from MODEL_PRICING_JSON environment variable."""
        custom_pricing = {
            "gpt-4o": 0.015,
            "gpt-4o-mini": 0.0005
        }
        
        with patch.dict(os.environ, {'MODEL_PRICING_JSON': json.dumps(custom_pricing)}):
            pricing = PricingManager()
            
            # Check config source
            assert pricing.config_source == "environment variable"
            
            # Check custom pricing is loaded
            assert pricing.pricing_data["gpt-4o"] == 0.015
            assert pricing.pricing_data["gpt-4o-mini"] == 0.0005
            
            # Test cost calculation
            cost = pricing.calculate_cost("gpt-4o", 1000)
            assert cost == 0.015

    def test_environment_variable_config_path(self):
        """Test loading pricing from MODEL_PRICING_CONFIG_PATH environment variable."""
        custom_pricing = {
            "gpt-4o": 0.020,
            "gpt-4o-mini": 0.0006
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(custom_pricing, f)
            temp_file = f.name
        
        try:
            with patch.dict(os.environ, {'MODEL_PRICING_CONFIG_PATH': temp_file}):
                pricing = PricingManager()
                
                # Check config source
                assert pricing.config_source == f"env file: {temp_file}"
                
                # Check custom pricing is loaded
                assert pricing.pricing_data["gpt-4o"] == 0.020
                assert pricing.pricing_data["gpt-4o-mini"] == 0.0006
                
                # Test cost calculation
                cost = pricing.calculate_cost("gpt-4o", 1000)
                assert cost == 0.020
                
        finally:
            Path(temp_file).unlink()

    def test_configuration_priority(self):
        """Test that configuration sources are loaded in correct priority order."""
        # Create a temporary file
        file_pricing = {"gpt-4o": 0.010}
        env_pricing = {"gpt-4o": 0.015}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(file_pricing, f)
            temp_file = f.name
        
        try:
            # Test priority: custom file > env file > env json > default
            with patch.dict(os.environ, {
                'MODEL_PRICING_CONFIG_PATH': temp_file,
                'MODEL_PRICING_JSON': json.dumps(env_pricing)
            }):
                # Custom file should take priority
                pricing = PricingManager(config_path=temp_file)
                assert pricing.pricing_data["gpt-4o"] == 0.010
                
                # Env file should take priority over env json
                pricing = PricingManager()
                assert pricing.pricing_data["gpt-4o"] == 0.010
                
                # Env json should take priority over default
                os.unlink(temp_file)  # Remove file so it falls back to env json
                pricing = PricingManager()
                assert pricing.pricing_data["gpt-4o"] == 0.015
                
        finally:
            if Path(temp_file).exists():
                Path(temp_file).unlink()

    def test_get_pricing(self):
        """Test getting pricing information."""
        pricing = PricingManager()
        
        # Test getting all pricing
        all_prices = pricing.get_pricing()
        assert isinstance(all_prices, dict)
        assert "gpt-4o" in all_prices
        
        # Test getting specific model pricing
        gpt4_price = pricing.get_pricing("gpt-4o")
        assert gpt4_price == 0.01
        
        # Test getting unknown model pricing
        unknown_price = pricing.get_pricing("unknown-model")
        assert unknown_price == 0.002

    def test_update_pricing(self):
        """Test updating pricing for existing models."""
        pricing = PricingManager()
        
        # Update existing model
        pricing.update_pricing("gpt-4o", 0.012)
        assert pricing.pricing_data["gpt-4o"] == 0.012
        
        # Test cost calculation with updated pricing
        cost = pricing.calculate_cost("gpt-4o", 1000)
        assert cost == 0.012

    def test_add_model(self):
        """Test adding pricing for new models."""
        pricing = PricingManager()
        
        # Add new model
        pricing.add_model("new-model", 0.005)
        assert pricing.pricing_data["new-model"] == 0.005
        
        # Test cost calculation with new model
        cost = pricing.calculate_cost("new-model", 1000)
        assert cost == 0.005

    def test_remove_model(self):
        """Test removing pricing for models."""
        pricing = PricingManager()
        
        # Remove existing model
        result = pricing.remove_model("gpt-4o")
        assert result is True
        assert "gpt-4o" not in pricing.pricing_data
        
        # Try to remove non-existent model
        result = pricing.remove_model("non-existent")
        assert result is False

    def test_export_config(self):
        """Test exporting configuration to JSON file."""
        pricing = PricingManager()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            pricing.export_config(temp_file)
            
            # Verify file was created and contains correct data
            assert Path(temp_file).exists()
            
            with open(temp_file, 'r') as f:
                exported_data = json.load(f)
            
            assert exported_data == pricing.pricing_data
            
        finally:
            Path(temp_file).unlink()

    def test_reload_config(self):
        """Test reloading configuration."""
        pricing = PricingManager()
        original_source = pricing.config_source
        
        # Create new config file
        new_pricing = {"gpt-4o": 0.025}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(new_pricing, f)
            temp_file = f.name
        
        try:
            # Reload with new config
            pricing.reload_config(temp_file)
            
            # Check that config was reloaded
            assert pricing.config_source == f"file: {temp_file}"
            assert pricing.pricing_data["gpt-4o"] == 0.025
            
        finally:
            Path(temp_file).unlink()

    def test_invalid_json_file(self):
        """Test handling of invalid JSON files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_file = f.name
        
        try:
            # Should fall back to default pricing
            pricing = PricingManager(config_path=temp_file)
            assert pricing.config_source == "default"
            assert "gpt-4o" in pricing.pricing_data
            
        finally:
            Path(temp_file).unlink()

    def test_nonexistent_file(self):
        """Test handling of non-existent files."""
        # Should fall back to default pricing
        pricing = PricingManager(config_path="nonexistent_file.json")
        assert pricing.config_source == "default"
        assert "gpt-4o" in pricing.pricing_data




class TestGetPricingManager:
    """Test cases for the get_pricing_manager function."""

    def test_get_pricing_manager_singleton(self):
        """Test that get_pricing_manager returns a singleton instance."""
        manager1 = get_pricing_manager()
        manager2 = get_pricing_manager()
        
        assert manager1 is manager2
        assert isinstance(manager1, PricingManager)

    def test_get_pricing_manager_with_custom_config(self):
        """Test that get_pricing_manager can be configured via environment variables."""
        custom_pricing = {"gpt-4o": 0.020}
        
        with patch.dict(os.environ, {'MODEL_PRICING_JSON': json.dumps(custom_pricing)}):
            # Reset global pricing manager to pick up new environment
            import sherpa_ai.cost_tracking.pricing as pricing_module
            pricing_module._default_pricing_manager = None
            
            manager = get_pricing_manager()
            assert manager.pricing_data["gpt-4o"] == 0.020
            
            # Reset global pricing manager
            pricing_module._default_pricing_manager = None


class TestPricingIntegration:
    """Integration tests for pricing system."""

    def test_pricing_with_different_token_amounts(self):
        """Test pricing calculations with various token amounts."""
        pricing = PricingManager()
        
        test_cases = [
            ("gpt-4o", 1, 0.00001),
            ("gpt-4o", 100, 0.001),
            ("gpt-4o", 1000, 0.01),
            ("gpt-4o", 10000, 0.1),
            ("gpt-4o-mini", 1000, 0.000375),
            ("claude-3-5-sonnet-20241022", 1000, 0.009),
        ]
        
        for model, tokens, expected_cost in test_cases:
            cost = pricing.calculate_cost(model, tokens)
            assert abs(cost - expected_cost) < 0.000001, f"Failed for {model} with {tokens} tokens"

    def test_pricing_case_insensitivity(self):
        """Test that pricing is case-insensitive."""
        pricing = PricingManager()
        
        models = ["gpt-4o", "GPT-4O", "Gpt-4O", "gPT-4o"]
        
        for model in models:
            cost = pricing.calculate_cost(model, 1000)
            assert cost == 0.01, f"Failed for model: {model}"

    def test_pricing_with_zero_tokens(self):
        """Test pricing calculation with zero tokens."""
        pricing = PricingManager()
        
        cost = pricing.calculate_cost("gpt-4o", 0)
        assert cost == 0.0

    def test_pricing_with_negative_tokens(self):
        """Test pricing calculation with negative tokens."""
        pricing = PricingManager()
        
        cost = pricing.calculate_cost("gpt-4o", -1000)
        assert cost == -0.01
