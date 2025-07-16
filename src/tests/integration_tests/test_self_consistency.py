from pydantic import BaseModel

from sherpa_ai.output_parsers.self_consistency.abstract_objects import AbstractObject
from sherpa_ai.output_parsers.self_consistency.concretizer import (
    MaximumLikelihoodConcretizer,
)
from sherpa_ai.output_parsers.self_consistency.object_aggregator import ObjectAggregator


class SimpleModel(BaseModel):
    name: str
    value: int


class NestedModel(BaseModel):
    title: str
    simple: SimpleModel


def test_abstract_multiple_nested_objects():
    """Test adding multiple objects with nested models."""
    aggregator = ObjectAggregator(obj_schema=NestedModel)

    nested1 = NestedModel(title="first", simple=SimpleModel(name="inner1", value=100))

    nested2 = NestedModel(title="second", simple=SimpleModel(name="inner2", value=200))
    nested3 = NestedModel(title="second", simple=SimpleModel(name="inner2", value=200))
    nested4 = NestedModel(title="second", simple=SimpleModel(name="inner2", value=300))

    aggregator.add_object(nested1)
    aggregator.add_object(nested2)
    aggregator.add_object(nested3)
    aggregator.add_object(nested4)

    abstract_object = AbstractObject.from_aggregator(aggregator)
    concretizer = MaximumLikelihoodConcretizer()
    concrete_obj = concretizer.concretize(abstract_object, return_dict=False)

    assert isinstance(concrete_obj, NestedModel)
    assert concrete_obj.title == "second"
    assert concrete_obj.simple.name == "inner2"
    assert concrete_obj.simple.value == 200


def test_abstract_multiple_nested_objects_weighted():
    """Test adding multiple objects with nested models and weights."""
    weight_map = {
        "title": {"first": 7.0, "second": 1.0},
        "simple": {
            "name": {"inner1": 1.0, "inner2": 2.0},
        },
    }

    aggregator = ObjectAggregator(obj_schema=NestedModel, value_weight_map=weight_map)
    nested1 = NestedModel(title="first", simple=SimpleModel(name="inner1", value=100))
    nested2 = NestedModel(title="second", simple=SimpleModel(name="inner2", value=200))
    nested3 = NestedModel(title="second", simple=SimpleModel(name="inner2", value=200))
    nested4 = NestedModel(title="second", simple=SimpleModel(name="inner2", value=300))

    aggregator.add_object(nested1)
    aggregator.add_object(nested2)
    aggregator.add_object(nested3)
    aggregator.add_object(nested4)

    abstract_object = AbstractObject.from_aggregator(aggregator)
    concretizer = MaximumLikelihoodConcretizer()
    concrete_obj = concretizer.concretize(abstract_object, return_dict=False)

    assert isinstance(concrete_obj, NestedModel)
    assert concrete_obj.title == "first"
    assert concrete_obj.simple.name == "inner2"
    assert concrete_obj.simple.value == 200
