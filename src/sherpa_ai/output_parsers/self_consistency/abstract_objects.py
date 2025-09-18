from collections import defaultdict
from typing import Union

from pydantic import BaseModel, ConfigDict

from sherpa_ai.output_parsers.self_consistency.abstractors import (
    AttributeAbstractor,
    CountingAttributeAbstractor,
)
from sherpa_ai.output_parsers.self_consistency.distributions import Distribution
from sherpa_ai.output_parsers.self_consistency.object_aggregator import ObjectAggregator


class AbstractObject(BaseModel):
    """
    Abstract object that maps each attribute into a distribution
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    obj_schema: type[BaseModel]
    """
    Schema of the object, used to validate the object.
    """

    obj_dict: dict[str, Union[Distribution, dict]] = {}

    @classmethod
    def from_aggregator(cls, obj_aggregator: ObjectAggregator) -> "AbstractObject":
        """
        Create an AbstractObject from an ObjectAggregator.

        Args:
            obj_aggregator (ObjectAggregator): The ObjectAggregator to convert.

        Returns:
            AbstractObject: An instance of AbstractObject with the aggregated data.
        """
        counting_abstractor = CountingAttributeAbstractor()
        # TODO: Support other types of abstractors based on the attribute type

        abstractor_map = defaultdict(lambda: counting_abstractor)

        # Recursively abstract the object dictionary using the abstractor map
        abstracted_dict = abstract_recursive(
            obj_aggregator.obj_dict, abstractor_map, obj_aggregator.value_weight_map
        )

        return cls(
            obj_schema=obj_aggregator.obj_schema,
            obj_dict=abstracted_dict,
        )


def abstract_recursive(
    obj_dict: dict[str, Union[list, dict]],
    abstractor_map: dict[str, AttributeAbstractor],
    value_weight_map: dict[str, Union[dict, float]] = {},
) -> dict[str, Union[list, Distribution]]:
    """
    Recursively abstract the object dictionary using the provided abstractor.
    Args:
        obj_dict (dict[str, Union[list, dict]]): The object dictionary to abstract.
        abstractor_map (dict[str, AttributeAbstractor]): A mapping of attribute names to abstractors.

    Returns:
        dict[str, Union[list, Distribution]]: The abstracted object dictionary.
    """  # noqa: E501
    abstracted_dict = {}
    for key, value in obj_dict.items():
        if isinstance(value, list):
            # If the value is a list, abstract it using the corresponding abstractor
            abstractor = abstractor_map[key]
            weight_map = value_weight_map.get(key, {})
            abstracted_dict[key] = abstractor.abstract(value, weight_map)
        elif isinstance(value, dict):
            # If the value is a dictionary, recursively abstract it
            abstracted_dict[key] = abstract_recursive(
                value, abstractor_map, value_weight_map.get(key, {})
            )
        else:
            raise TypeError(f"Unsupported type for key '{key}': {type(value)}")
    return abstracted_dict
