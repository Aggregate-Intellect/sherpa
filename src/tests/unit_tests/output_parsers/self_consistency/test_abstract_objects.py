from pydantic import BaseModel

from sherpa_ai.output_parsers.self_consistency.abstract_objects import AbstractObject
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

    assert abstract_object.obj_dict["title"].get_probability("first") == 0.25
    assert abstract_object.obj_dict["title"].get_probability("second") == 0.75
    assert abstract_object.obj_dict["title"].get_mode() == "second"
    assert abstract_object.obj_dict["simple"]["name"].get_probability("inner1") == 0.25
    assert abstract_object.obj_dict["simple"]["name"].get_probability("inner2") == 0.75
    assert abstract_object.obj_dict["simple"]["name"].get_mode() == "inner2"
    assert abstract_object.obj_dict["simple"]["value"].get_probability(100) == 0.25
    assert abstract_object.obj_dict["simple"]["value"].get_probability(200) == 0.5
    assert abstract_object.obj_dict["simple"]["value"].get_probability(300) == 0.25
    assert abstract_object.obj_dict["simple"]["value"].get_mode() == 200
