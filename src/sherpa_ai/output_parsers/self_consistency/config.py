from pydantic import BaseModel, Field
from typing import Literal


class ListConfig(BaseModel):
    """Configuration for individual list attributes in self-consistency processing.
    
    This class defines how list attributes should be processed during the
    self-consistency aggregation and concretization process.
    
    Attributes:
        top_k: Number of top items to select when using "top_k" strategy.
               Defaults to 0 (which means use default behavior).
        threshold: Minimum frequency threshold when using "threshold" strategy.
                  Defaults to 2.0.
        strategy: The strategy to use for selecting items from list attributes.
                 Either "top_k" or "threshold". Defaults to "top_k".
    """
    top_k: int = Field(default=0, description="Number of top items to select")
    threshold: float = Field(default=2.0, description="Minimum frequency threshold")
    strategy: Literal["top_k", "threshold"] = Field(
        default="top_k", 
        description="Strategy for selecting items from list attributes"
    )


class SelfConsistencyConfig(BaseModel):
    """Configuration for self-consistency processing.
    
    This class provides a structured way to configure self-consistency
    behavior, particularly for list attributes. It replaces the previous
    dict-based configuration approach.
    
    Attributes:
        list_config: Dictionary mapping field names to their list processing
                    configurations. Defaults to an empty dictionary.
    """
    list_config: dict[str, ListConfig] = Field(
        default_factory=dict,
        description="Configuration for list attributes by field name"
    )
    
    def get_list_config(self, field_path: str) -> ListConfig:
        """Get the list configuration for a specific field path.
        
        Args:
            field_path: The path to the field (e.g., "tags" or "nested.field")
            
        Returns:
            ListConfig: The configuration for the field, or default if not specified
        """
        return self.list_config.get(field_path, ListConfig())
    
    def has_list_config(self, field_path: str) -> bool:
        """Check if a field has specific list configuration.
        
        Args:
            field_path: The path to the field
            
        Returns:
            bool: True if the field has specific configuration, False otherwise
        """
        return field_path in self.list_config
