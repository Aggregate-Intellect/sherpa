import copy
from abc import ABC, abstractmethod
from typing import Any, Union, Dict, Optional

import pydash
from pydantic import BaseModel

from sherpa_ai.output_parsers.self_consistency.abstract_objects import AbstractObject
from sherpa_ai.output_parsers.self_consistency.distributions import Distribution, CountDistribution


class Concretizer(ABC):
    @abstractmethod
    def concretize(
        self, abstract_object: AbstractObject, return_dict: bool = False
    ) -> Union[BaseModel, dict[str, Any]]:
        """
        Concretize an abstract object into a concrete object.

        Args:
            abstract_object (AbstractObject): The abstract object to concretize.


        Returns:
            BaseModel: A concrete object that matches the schema and is sampled from
                the distributions in the abstract object.
        """
        pass


class MaximumLikelihoodConcretizer(Concretizer):
    def __init__(self, list_config: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        Initialize the MaximumLikelihoodConcretizer.
        
        Args:
            list_config: Configuration for list attributes. Format:
                {
                    "field_name": {
                        "top_k": 3,  # Get top-k items
                        "threshold": 2.0,  # Or get items above threshold
                        "strategy": "top_k"  # or "threshold"
                    }
                }
        """
        self.list_config = list_config or {}
    
    def concretize(
        self, abstract_object: AbstractObject, return_dict: bool = False
    ) -> Union[BaseModel, dict[str, Any]]:
        """
        Concretize an abstract object by selecting the most likely value for each attribute.
        For list attributes, uses top-k or threshold-based selection.

        Args:
            abstract_object (AbstractObject): The abstract object to concretize.

        Returns:
            BaseModel: A concrete object with the most likely values for each attribute.
        """  # noqa: E501

        def get_most_likely_value(value, field_path=""):
            if isinstance(value, CountDistribution):
                # Handle list attributes
                field_config = self.list_config.get(field_path, {})
                strategy = field_config.get("strategy", "top_k")
                
                if strategy == "top_k":
                    top_k = field_config.get("top_k", 1)
                    return value.get_top_k(top_k)
                elif strategy == "threshold":
                    threshold = field_config.get("threshold", 1.0)
                    return value.get_above_threshold(threshold)
                else:
                    # Default to top-1 for backward compatibility
                    return [value.get_mode()]
            elif isinstance(value, Distribution):
                return value.get_mode()
            else:
                return value

        concrete_obj = copy.deepcopy(abstract_object.obj_dict)
        
        # Use a custom function to handle field paths for list configuration
        def map_values_with_path(obj, path=""):
            if isinstance(obj, dict):
                result = {}
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    if isinstance(value, dict):
                        result[key] = map_values_with_path(value, current_path)
                    else:
                        result[key] = get_most_likely_value(value, current_path)
                return result
            else:
                return get_most_likely_value(obj, path)
        
        concrete_obj = map_values_with_path(concrete_obj)

        if return_dict:
            return concrete_obj
        else:
            return abstract_object.obj_schema.model_validate(concrete_obj)
