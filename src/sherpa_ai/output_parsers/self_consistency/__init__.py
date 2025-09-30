from typing import Optional, Union, Dict, Any

from pydantic import BaseModel

from sherpa_ai.output_parsers.self_consistency.abstract_objects import AbstractObject
from sherpa_ai.output_parsers.self_consistency.concretizer import (
    Concretizer,
    MaximumLikelihoodConcretizer,
)
from sherpa_ai.output_parsers.self_consistency.object_aggregator import ObjectAggregator
from sherpa_ai.output_parsers.self_consistency.config import SelfConsistencyConfig, ListConfig


def convert_list_config_from_dict(list_config: Optional[Dict[str, Dict[str, Any]]]) -> Optional[SelfConsistencyConfig]:
    """Convert dict-based list_config to SelfConsistencyConfig for compatibility.
    
    Args:
        list_config: Dict-based configuration parameter
        
    Returns:
        SelfConsistencyConfig or None if list_config is None
    """
    if list_config is None:
        return None
    
    converted_config = {}
    for field_name, field_config in list_config.items():
        converted_config[field_name] = ListConfig(
            top_k=field_config.get("top_k", 0),
            threshold=field_config.get("threshold", 2.0),
            strategy=field_config.get("strategy", "top_k")
        )
    
    return SelfConsistencyConfig(list_config=converted_config)


def run_self_consistency(
    objects: list[BaseModel],
    schema: type[BaseModel],
    aggregator_cls: type[ObjectAggregator] = ObjectAggregator,
    concretizer: Optional[Concretizer] = None,
    value_weight_map: dict[str, Union[dict, float]] = {},
    config: Optional[SelfConsistencyConfig] = None,
) -> BaseModel:
    """
    Run self-consistency on a list of objects using the provided schema and configuration.

    Args:
        objects (list[BaseModel]): List of objects to process.
        schema (type[BaseModel]): Pydantic schema for validation.
        aggregator_cls (type[ObjectAggregator], optional): Class to use for aggregation. Defaults to ObjectAggregator.
        concretizer (Optional[Concretizer], optional): Concretizer to use for final output. Defaults to MaximumLikelihoodConcretizer.
        value_weight_map (dict[str, Union[dict, float]], optional): Weight map for each attribute of the object. Defaults to {}.
        config (Optional[SelfConsistencyConfig], optional): Configuration for self-consistency processing.
            If None, default configuration will be used.

    Returns:
        BaseModel: The final concrete object after self-consistency processing (instance of `schema`).
    """  # noqa: E501
    
    # Validate input objects against the schema
    for obj in objects:
        if not isinstance(obj, schema):
            raise ValueError(f"Object {obj} does not match schema {schema}")

    if not concretizer:
        concretizer = MaximumLikelihoodConcretizer(config=config)
    aggregator = aggregator_cls(obj_schema=schema, value_weight_map=value_weight_map)

    for obj in objects:
        aggregator.add_object(obj)

    # the abstraction-concretization process
    abstract_object = AbstractObject.from_aggregator(aggregator)
    concrete_obj = concretizer.concretize(abstract_object, return_dict=False)

    return concrete_obj


__all__ = [
    "MaximumLikelihoodConcretizer",
    "ObjectAggregator",
    "AbstractObject",
    "run_self_consistency",
    "SelfConsistencyConfig",
    "ListConfig",
]
