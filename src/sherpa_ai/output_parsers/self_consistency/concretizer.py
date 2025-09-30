import copy
from abc import ABC, abstractmethod
from typing import Any, Union, Dict, Optional

import pydash
from pydantic import BaseModel

from sherpa_ai.output_parsers.self_consistency.abstract_objects import AbstractObject
from sherpa_ai.output_parsers.self_consistency.distributions import Distribution, CountDistribution
from sherpa_ai.output_parsers.self_consistency.config import SelfConsistencyConfig


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
    def __init__(self, config: Optional[SelfConsistencyConfig] = None):
        """
        Initialize the MaximumLikelihoodConcretizer.
        
        Args:
            config: Configuration for self-consistency processing.
                   If None, default configuration will be used.
        """
        self.config = config or SelfConsistencyConfig()
    
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
                field_config = self.config.get_list_config(field_path)
                strategy = field_config.strategy
                
                if strategy == "top_k":
                    top_k = field_config.top_k
                    if top_k > 0:
                        return value.get_top_k(top_k)
                    else:
                        # Default to top-1 for backward compatibility
                        return [value.get_mode()]
                elif strategy == "threshold":
                    threshold = field_config.threshold
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
