"""Pricing module for LLM cost calculation."""

import json
import os
from typing import Dict, Optional, Any
from pathlib import Path

from loguru import logger
import sherpa_ai.config as cfg
from pydantic import BaseModel, Field, field_validator


class ModelPricing(BaseModel):
    """Individual model pricing configuration."""
    
    input_price_per_1k: float = Field(..., ge=0, description="Input token price per 1k tokens")
    output_price_per_1k: float = Field(..., ge=0, description="Output token price per 1k tokens")
    
    @field_validator('input_price_per_1k', 'output_price_per_1k')
    @classmethod
    def validate_reasonable_prices(cls, v):
        """Validate that prices are within reasonable bounds."""
        if v > 1.0:  # $1 per 1k tokens is very high
            logger.warning(f"Price {v} seems unusually high (>$1 per 1k tokens)")
        return v


class PricingConfig(BaseModel):
    """Model for the complete pricing configuration."""
    
    models: Dict[str, ModelPricing] = Field(..., description="Model pricing configurations")
    
    @field_validator('models')
    @classmethod
    def validate_non_empty_models(cls, v):
        """Validate that at least one model is configured."""
        if not v:
            raise ValueError("At least one model must be configured")
        return v
    
    @field_validator('models')
    @classmethod
    def validate_model_names(cls, v):
        """Validate that model names are reasonable."""
        for model_name in v.keys():
            if not model_name or len(model_name.strip()) == 0:
                raise ValueError("Model names cannot be empty")
            if len(model_name) > 100:
                raise ValueError(f"Model name '{model_name}' is too long (max 100 characters)")
        return v
    
    def get_model_pricing(self, model_name: str) -> ModelPricing:
        """Get pricing for a specific model."""
        if model_name not in self.models:
            raise ValueError(f"Model '{model_name}' not found in pricing configuration")
        return self.models[model_name]
    
    def list_models(self) -> list:
        """Get list of configured model names."""
        return list(self.models.keys())
    
    def validate_model_exists(self, model_name: str) -> bool:
        """Check if a model exists in the configuration."""
        return model_name in self.models


def validate_pricing_config(config_data: Dict[str, Any]) -> PricingConfig:
    """
    Validate pricing configuration data using Pydantic schema.
    
    Args:
        config_data: Raw configuration data (dict)
        
    Returns:
        PricingConfig: Validated pricing configuration
        
    Raises:
        ValueError: If configuration is invalid
    """
    try:
        return PricingConfig(models=config_data)
    except Exception as e:
        logger.error(f"Pricing configuration validation failed: {e}")
        raise ValueError(f"Invalid pricing configuration: {e}")


def validate_pricing_file(file_path: str) -> PricingConfig:
    """
    Validate pricing configuration from a JSON file.
    
    Args:
        file_path: Path to the JSON configuration file
        
    Returns:
        PricingConfig: Validated pricing configuration
        
    Raises:
        ValueError: If file is invalid or configuration is malformed
    """
    if not Path(file_path).exists():
        raise ValueError(f"Pricing configuration file not found: {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            config_data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in pricing configuration file: {e}")
    except Exception as e:
        raise ValueError(f"Failed to read pricing configuration file: {e}")
    
    return validate_pricing_config(config_data)


class PricingManager:
    """Pricing manager for LLM cost calculations."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the pricing manager."""
        self.pricing_data = {}
        self._load_pricing_config(config_path)
    
    def _load_pricing_config(self, config_path: Optional[str] = None):
        """Load pricing configuration from JSON file."""
        # Check environment variables first
        if 'MODEL_PRICING_JSON' in os.environ:
            try:
                env_pricing = json.loads(os.environ['MODEL_PRICING_JSON'])
                # Validate configuration using Pydantic schema
                validated_config = validate_pricing_config(env_pricing)
                self.pricing_data = {model: {
                    "input_price_per_1k": pricing.input_price_per_1k,
                    "output_price_per_1k": pricing.output_price_per_1k
                } for model, pricing in validated_config.models.items()}
                logger.info("Loaded and validated pricing config from MODEL_PRICING_JSON environment variable")
                return
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Invalid JSON or configuration in MODEL_PRICING_JSON: {e}")
        
        if config_path and Path(config_path).exists():
            self._load_from_file(config_path)
        else:
            # Use default config file
            default_path = Path(__file__).parent / "../../conf/pricing_config.json"
            if default_path.exists():
                self._load_from_file(str(default_path))
            else:
                logger.warning("No pricing config found, using empty pricing data")
                self.pricing_data = {}
    
    def _load_from_file(self, file_path: str):
        """Load pricing data from JSON file."""
        try:
            with open(file_path, 'r') as f:
                config_data = json.load(f)
            
            # Validate configuration using Pydantic schema
            validated_config = validate_pricing_config(config_data)
            self.pricing_data = {model: {
                "input_price_per_1k": pricing.input_price_per_1k,
                "output_price_per_1k": pricing.output_price_per_1k
            } for model, pricing in validated_config.models.items()}
            
            logger.info(f"Loaded and validated pricing config from: {file_path}")
        except Exception as e:
            logger.error(f"Failed to load or validate pricing config from {file_path}: {e}")
            self.pricing_data = {}
    
    def _convert_legacy_pricing(self, pricing_data: dict) -> dict:
        """Convert legacy pricing format to new format."""
        converted = {}
        for model, price in pricing_data.items():
            if isinstance(price, (int, float)):
                # Legacy format: single price per model
                # For backward compatibility, use the same price for both input and output
                converted[model] = {
                    "input_price_per_1k": price,
                    "output_price_per_1k": price
                }
            elif isinstance(price, dict) and "input_price_per_1k" in price:
                # New format: already has separate input/output prices
                converted[model] = price
            else:
                logger.warning(f"Unknown pricing format for model {model}: {price}")
        return converted
    
    def calculate_cost(self, model_name: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for a model call with separate input/output tokens.
        
        Args:
            model_name: Name of the model.
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.
            
        Returns:
            float: Total cost in USD.
        """
        if model_name not in self.pricing_data:
            logger.warning(f"Unknown model: {model_name}")
            return 0.0
        
        model_config = self.pricing_data[model_name]
        input_price_per_1k = model_config.get("input_price_per_1k", 0.0)
        output_price_per_1k = model_config.get("output_price_per_1k", 0.0)
        
        input_cost = (input_tokens / 1000.0) * input_price_per_1k
        output_cost = (output_tokens / 1000.0) * output_price_per_1k
        
        return input_cost + output_cost
    
    def calculate_cost_from_usage_metadata(self, model_name: str, usage_metadata: Dict[str, Any]) -> float:
        """Calculate cost from usage metadata (thin wrapper).
        
        Args:
            model_name: Name of the model.
            usage_metadata: Usage metadata from callback.
            
        Returns:
            float: Total cost in USD.
        """
        input_tokens = usage_metadata.get("input_tokens", 0)
        output_tokens = usage_metadata.get("output_tokens", 0)
        return self.calculate_cost(model_name, input_tokens, output_tokens)
    
    def get_pricing(self) -> Dict[str, Any]:
        """Get current pricing configuration."""
        return self.pricing_data.copy()
    
    def update_pricing(self, new_pricing: Dict[str, Any]):
        """Update pricing configuration."""
        self.pricing_data.update(new_pricing)
        logger.info("Pricing configuration updated")
    
    def add_model(self, model_name: str, input_price_per_1k: float, output_price_per_1k: float):
        """Add a new model to pricing configuration."""
        self.pricing_data[model_name] = {
            "input_price_per_1k": input_price_per_1k,
            "output_price_per_1k": output_price_per_1k
        }
        logger.info(f"Added model {model_name} to pricing configuration")
