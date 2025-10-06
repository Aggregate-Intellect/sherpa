import pytest
from pydantic import BaseModel

from sherpa_ai.output_parsers.self_consistency import ObjectAggregator


class SimpleModel(BaseModel):
    name: str
    value: int


class NestedModel(BaseModel):
    title: str
    simple: SimpleModel


def test_init_creates_correct_structure():
    """Test that the constructor initializes the object_dict correctly."""
    aggregator = ObjectAggregator(obj_schema=SimpleModel)

    assert aggregator.obj_schema == SimpleModel
    assert isinstance(aggregator.obj_dict, dict)
    assert "name" in aggregator.obj_dict
    assert "value" in aggregator.obj_dict
    assert isinstance(aggregator.obj_dict["name"], list)
    assert isinstance(aggregator.obj_dict["value"], list)
    assert len(aggregator.obj_dict["name"]) == 0
    assert len(aggregator.obj_dict["value"]) == 0


def test_init_with_nested_model():
    """Test initialization with a nested model schema."""
    aggregator = ObjectAggregator(obj_schema=NestedModel)

    assert aggregator.obj_schema == NestedModel
    assert "title" in aggregator.obj_dict
    assert "simple" in aggregator.obj_dict
    assert isinstance(aggregator.obj_dict["title"], list)
    assert isinstance(aggregator.obj_dict["simple"], dict)
    assert "name" in aggregator.obj_dict["simple"]
    assert "value" in aggregator.obj_dict["simple"]


def test_add_object_with_valid_object():
    """Test adding a valid object to the aggregator."""
    aggregator = ObjectAggregator(obj_schema=SimpleModel)
    obj = SimpleModel(name="test", value=42)

    aggregator.add_object(obj)

    assert len(aggregator.obj_dict["name"]) == 1
    assert len(aggregator.obj_dict["value"]) == 1
    assert aggregator.obj_dict["name"][0] == "test"
    assert aggregator.obj_dict["value"][0] == 42


def test_add_multiple_objects():
    """Test adding multiple objects to the aggregator."""
    aggregator = ObjectAggregator(obj_schema=SimpleModel)
    obj1 = SimpleModel(name="test1", value=42)
    obj2 = SimpleModel(name="test2", value=84)

    aggregator.add_object(obj1)
    aggregator.add_object(obj2)

    assert len(aggregator.obj_dict["name"]) == 2
    assert len(aggregator.obj_dict["value"]) == 2
    assert aggregator.obj_dict["name"] == ["test1", "test2"]
    assert aggregator.obj_dict["value"] == [42, 84]


def test_add_object_with_wrong_type():
    """Test adding an object with wrong type raises ValueError."""

    class OtherModel(BaseModel):
        field: str

    aggregator = ObjectAggregator(obj_schema=SimpleModel)
    wrong_obj = OtherModel(field="wrong")

    with pytest.raises(ValueError) as excinfo:
        aggregator.add_object(wrong_obj)

    assert f"Object must be of type {SimpleModel.__name__}" in str(excinfo.value)


def test_add_object_with_nested_model():
    """Test adding an object with nested model."""
    aggregator = ObjectAggregator(obj_schema=NestedModel)
    simple = SimpleModel(name="inner", value=100)
    nested = NestedModel(title="outer", simple=simple)

    aggregator.add_object(nested)

    assert len(aggregator.obj_dict["title"]) == 1
    assert aggregator.obj_dict["title"][0] == "outer"
    assert len(aggregator.obj_dict["simple"]["name"]) == 1
    assert len(aggregator.obj_dict["simple"]["value"]) == 1
    assert aggregator.obj_dict["simple"]["name"][0] == "inner"
    assert aggregator.obj_dict["simple"]["value"][0] == 100


def test_add_multiple_nested_objects():
    """Test adding multiple objects with nested models."""
    aggregator = ObjectAggregator(obj_schema=NestedModel)

    nested1 = NestedModel(title="first", simple=SimpleModel(name="inner1", value=100))

    nested2 = NestedModel(title="second", simple=SimpleModel(name="inner2", value=200))

    aggregator.add_object(nested1)
    aggregator.add_object(nested2)

    assert len(aggregator.obj_dict["title"]) == 2
    assert aggregator.obj_dict["title"] == ["first", "second"]
    assert len(aggregator.obj_dict["simple"]["name"]) == 2
    assert len(aggregator.obj_dict["simple"]["value"]) == 2
    assert aggregator.obj_dict["simple"]["name"] == ["inner1", "inner2"]
    assert aggregator.obj_dict["simple"]["value"] == [100, 200]
