import copy
from abc import ABC, abstractmethod
from typing import Any, Union

import pydash
from pydantic import BaseModel

from sherpa_ai.output_parsers.self_consistency.abstract_objects import AbstractObject
from sherpa_ai.output_parsers.self_consistency.distributions import Distribution


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
    def concretize(
        self, abstract_object: AbstractObject, return_dict: bool = False
    ) -> Union[BaseModel, dict[str, Any]]:
        """
        Concretize an abstract object by selecting the most likely value for each attribute.

        Args:
            abstract_object (AbstractObject): The abstract object to concretize.

        Returns:
            BaseModel: A concrete object with the most likely values for each attribute.
        """  # noqa: E501

        def get_most_likely_value(value):
            if isinstance(value, Distribution):
                return value.get_mode()
            else:
                return value

        concrete_obj = copy.deepcopy(abstract_object.obj_dict)
        pydash.map_values_deep(
            concrete_obj,
            get_most_likely_value,
        )

        if return_dict:
            return concrete_obj
        else:
            return abstract_object.obj_schema.model_validate(concrete_obj)
