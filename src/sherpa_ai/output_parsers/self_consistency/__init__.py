from typing import Optional, Union

from pydantic import BaseModel

from sherpa_ai.output_parsers.self_consistency.abstract_objects import AbstractObject
from sherpa_ai.output_parsers.self_consistency.concretizer import (
    Concretizer,
    MaximumLikelihoodConcretizer,
)
from sherpa_ai.output_parsers.self_consistency.object_aggregator import ObjectAggregator


def run_self_consistency(
    objects: list[BaseModel],
    schema: type[BaseModel],
    aggregator_cls: type[ObjectAggregator] = ObjectAggregator,
    concretizer: Optional[Concretizer] = None,
    value_weight_map: dict[str, Union[dict, float]] = {},
) -> BaseModel:
    """
    Run self-consistency on a list of objects using the provided schema and configuration.

    Args:
        objects (list[BaseModel]): List of objects to process.
        schema (type[BaseModel]): Pydantic schema for validation.
        aggregator_cls (type[ObjectAggregator], optional): Class to use for aggregation. Defaults to ObjectAggregator.
        concretizer (Optional[Concretizer], optional): Concretizer to use for final output. Defaults to MaximumLikelihoodConcretizer.
        value_weight_map (dict[str, Union[dict, float]], optional): Weight map for each attribute of the object. Defaults to {}.

    Returns:
        BaseModel: The final concrete object after self-consistency processing (instance of `schema`).
    """  # noqa: E501
    # Validate input objects against the schema
    for obj in objects:
        if not isinstance(obj, schema):
            raise ValueError(f"Object {obj} does not match schema {schema}")

    if not concretizer:
        concretizer = MaximumLikelihoodConcretizer()
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
]
