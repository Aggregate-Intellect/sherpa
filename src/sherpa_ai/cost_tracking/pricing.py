"""Configurable pricing module for LLM cost calculation.

This module provides a flexible pricing system that can be configured through
environment variables, configuration files, or programmatically. It supports
different pricing models and can be easily updated without code changes.

Example:
    >>> from sherpa_ai.cost_tracking.pricing import PricingManager
    >>> pricing = PricingManager()
    >>> cost = pricing.calculate_cost("gpt-4o", 1000)
    >>> print(f"Cost: ${cost:.4f}")
    Cost: $0.0100
"""

import os
import json
from typing import Dict, Optional, Union, Any
from pathlib import Path

from loguru import logger
import sherpa_ai.config as cfg


class PricingManager:
    """Manages LLM pricing configuration and cost calculations.
    
    This class provides a flexible way to manage pricing for different LLM models.
    It supports multiple configuration sources with fallback mechanisms.
    
    Attributes:
        pricing_data (Dict[str, float]): Current pricing configuration.
        config_source (str): Source of the current pricing configuration.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the pricing manager.
        
        Args:
            config_path: Optional path to a JSON pricing configuration file.
                        If not provided, will use environment variables or defaults.
        """
        self.pricing_data = {}
        self.config_source = "default"
        self._load_pricing_config(config_path)
    
    def _load_pricing_config(self, config_path: Optional[str] = None):
        """Load pricing configuration from various sources.
        
        Priority order:
        1. Custom config file (if provided)
        2. Config file from MODEL_PRICING_CONFIG_PATH environment variable
        3. Environment variable (MODEL_PRICING_JSON)
        4. Default pricing table
        
        Args:
            config_path: Optional path to a JSON pricing configuration file.
        """
        # Try custom config file first
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    self.pricing_data = json.load(f)
                self.config_source = f"file: {config_path}"
                logger.info(f"Loaded pricing config from file: {config_path}")
                return
            except Exception as e:
                logger.warning(f"Failed to load pricing config from {config_path}: {e}")
        
        # Try config file from environment variable
        env_config_path = os.getenv('MODEL_PRICING_CONFIG_PATH')
        if env_config_path and Path(env_config_path).exists():
            try:
                with open(env_config_path, 'r') as f:
                    self.pricing_data = json.load(f)
                self.config_source = f"env file: {env_config_path}"
                logger.info(f"Loaded pricing config from environment file: {env_config_path}")
                return
            except Exception as e:
                logger.warning(f"Failed to load pricing config from {env_config_path}: {e}")
        
        # Try environment variable
        env_pricing = os.getenv('MODEL_PRICING_JSON')
        if env_pricing:
            try:
                self.pricing_data = json.loads(env_pricing)
                self.config_source = "environment variable"
                logger.info("Loaded pricing config from environment variable")
                return
            except Exception as e:
                logger.warning(f"Failed to parse MODEL_PRICING_JSON: {e}")
        
        # Fall back to default pricing
        self._load_default_pricing()
    
    def _load_default_pricing(self):
        """Load default pricing configuration.
        
        This provides a reasonable default pricing table that can be overridden
        through configuration files or environment variables.
        """
        self.pricing_data = {
            # OpenAI Models (cost per 1K tokens)
            "gpt-4o": 0.01,  # Average of input/output
            "gpt-4o-mini": 0.000375,  # Average of input/output
            "gpt-4-turbo": 0.02,  # Average of input/output
            "gpt-4": 0.045,  # Average of input/output
            "gpt-3.5-turbo": 0.00175,  # Average of input/output
            "gpt-3.5-turbo-16k": 0.0035,  # Average of input/output
            
            # Anthropic Models
            "claude-3-5-sonnet-20241022": 0.009,  # Average of input/output
            "claude-3-5-haiku-20241022": 0.0024,  # Average of input/output
            "claude-3-opus-20240229": 0.045,  # Average of input/output
            
            # Google Models
            "gemini-1.5-pro": 0.003125,  # Average of input/output
            "gemini-1.5-flash": 0.0001875,  # Average of input/output
        }
        self.config_source = "default"
        logger.info("Using default pricing configuration")
    
    def calculate_cost(self, model_name: str, tokens: int) -> float:
        """Calculate cost for a given model and token count.
        
        Args:
            model_name: Name of the model (case-insensitive).
            tokens: Number of tokens.
            
        Returns:
            Cost in USD.
            
        Example:
            >>> pricing = PricingManager()
            >>> cost = pricing.calculate_cost("gpt-4o", 1000)
            >>> print(f"Cost: ${cost:.4f}")
            Cost: $0.0100
        """
        # Normalize model name (lowercase for consistent lookup)
        model_key = model_name.lower()
        
        # Get cost per 1K tokens, default to a reasonable estimate
        cost_per_1k = self.pricing_data.get(model_key, 0.002)
        
        # Calculate total cost
        total_cost = (tokens / 1000.0) * cost_per_1k
        
        logger.debug(f"Cost calculation: {model_name} -> {tokens} tokens -> ${total_cost:.6f}")
        
        return total_cost
    
    def get_pricing(self, model_name: Optional[str] = None) -> Union[Dict[str, float], float]:
        """Get pricing information for a model or all models.
        
        Args:
            model_name: Name of the model. If None, returns all pricing data.
            
        Returns:
            Pricing data for the specified model or all models.
            
        Example:
            >>> pricing = PricingManager()
            >>> gpt4_price = pricing.get_pricing("gpt-4o")
            >>> all_prices = pricing.get_pricing()
        """
        if model_name is None:
            return self.pricing_data.copy()
        
        model_key = model_name.lower()
        return self.pricing_data.get(model_key, 0.002)
    
    def update_pricing(self, model_name: str, cost_per_1k: float):
        """Update pricing for a specific model.
        
        Args:
            model_name: Name of the model.
            cost_per_1k: Cost per 1K tokens in USD.
            
        Example:
            >>> pricing = PricingManager()
            >>> pricing.update_pricing("gpt-4o", 0.012)
        """
        model_key = model_name.lower()
        self.pricing_data[model_key] = cost_per_1k
        logger.info(f"Updated pricing for {model_name}: ${cost_per_1k:.6f} per 1K tokens")
    
    def add_model(self, model_name: str, cost_per_1k: float):
        """Add pricing for a new model.
        
        Args:
            model_name: Name of the model.
            cost_per_1k: Cost per 1K tokens in USD.
            
        Example:
            >>> pricing = PricingManager()
            >>> pricing.add_model("new-model", 0.005)
        """
        self.update_pricing(model_name, cost_per_1k)
    
    def remove_model(self, model_name: str) -> bool:
        """Remove pricing for a model.
        
        Args:
            model_name: Name of the model to remove.
            
        Returns:
            True if the model was removed, False if it wasn't found.
            
        Example:
            >>> pricing = PricingManager()
            >>> removed = pricing.remove_model("old-model")
        """
        model_key = model_name.lower()
        if model_key in self.pricing_data:
            del self.pricing_data[model_key]
            logger.info(f"Removed pricing for {model_name}")
            return True
        return False
    
    def get_config_source(self) -> str:
        """Get the source of the current pricing configuration.
        
        Returns:
            String describing the configuration source.
        """
        return self.config_source
    
    def export_config(self, file_path: str):
        """Export current pricing configuration to a JSON file.
        
        Args:
            file_path: Path where to save the configuration file.
            
        Example:
            >>> pricing = PricingManager()
            >>> pricing.export_config("pricing_config.json")
        """
        try:
            with open(file_path, 'w') as f:
                json.dump(self.pricing_data, f, indent=2)
            logger.info(f"Exported pricing config to {file_path}")
        except Exception as e:
            logger.error(f"Failed to export pricing config to {file_path}: {e}")
            raise
    
    def reload_config(self, config_path: Optional[str] = None):
        """Reload pricing configuration from the specified source.
        
        Args:
            config_path: Optional path to a JSON pricing configuration file.
                        If not provided, will reload from the same source used initially.
        """
        self._load_pricing_config(config_path)
        logger.info(f"Reloaded pricing configuration from {self.config_source}")


# Global pricing manager instance for convenience
_default_pricing_manager = None


def get_pricing_manager() -> PricingManager:
    """Get the global pricing manager instance.
    
    Returns:
        Global PricingManager instance.
    """
    global _default_pricing_manager
    if _default_pricing_manager is None:
        _default_pricing_manager = PricingManager()
    return _default_pricing_manager
