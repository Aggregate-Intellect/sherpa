from pydantic import BaseModel

from sherpa_ai.output_parsers.self_consistency import run_self_consistency
from sherpa_ai.output_parsers.self_consistency.abstract_objects import AbstractObject
from sherpa_ai.output_parsers.self_consistency.concretizer import (
    MaximumLikelihoodConcretizer,
)
from sherpa_ai.output_parsers.self_consistency.object_aggregator import ObjectAggregator
from sherpa_ai.output_parsers.self_consistency.config import SelfConsistencyConfig, ListConfig


class SimpleModel(BaseModel):
    name: str
    value: int


class NestedModel(BaseModel):
    title: str
    simple: SimpleModel


class ModelWithList(BaseModel):
    name: str
    tags: list[str]
    scores: list[int]


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


def test_run_self_consistency():
    nested1 = NestedModel(title="first", simple=SimpleModel(name="inner1", value=100))
    nested2 = NestedModel(title="second", simple=SimpleModel(name="inner2", value=200))
    nested3 = NestedModel(title="second", simple=SimpleModel(name="inner2", value=200))
    nested4 = NestedModel(title="second", simple=SimpleModel(name="inner2", value=300))

    objects = [nested1, nested2, nested3, nested4]

    concrete_obj = run_self_consistency(objects, schema=NestedModel)

    assert isinstance(concrete_obj, NestedModel)
    assert concrete_obj.title == "second"
    assert concrete_obj.simple.name == "inner2"
    assert concrete_obj.simple.value == 200


def test_run_self_consistency_weighted():
    weight_map = {
        "title": {"first": 7.0, "second": 1.0},
        "simple": {
            "name": {"inner1": 1.0, "inner2": 2.0},
        },
    }

    nested1 = NestedModel(title="first", simple=SimpleModel(name="inner1", value=100))
    nested2 = NestedModel(title="second", simple=SimpleModel(name="inner2", value=200))
    nested3 = NestedModel(title="second", simple=SimpleModel(name="inner2", value=200))
    nested4 = NestedModel(title="second", simple=SimpleModel(name="inner2", value=300))

    objects = [nested1, nested2, nested3, nested4]

    concrete_obj = run_self_consistency(
        objects, schema=NestedModel, value_weight_map=weight_map
    )

    assert isinstance(concrete_obj, NestedModel)
    assert concrete_obj.title == "first"
    assert concrete_obj.simple.name == "inner2"
    assert concrete_obj.simple.value == 200


def test_self_consistency_with_list_attributes():
    """Test self-consistency with list attributes using top-k strategy."""
    # Create objects with list attributes
    obj1 = ModelWithList(name="Alice", tags=["python", "ml", "ai"], scores=[85, 90, 88])
    obj2 = ModelWithList(name="Alice", tags=["python", "data", "ml"], scores=[85, 92, 88])
    obj3 = ModelWithList(name="Alice", tags=["python", "ml", "nlp"], scores=[85, 90, 89])
    obj4 = ModelWithList(name="Alice", tags=["python", "ai", "data"], scores=[85, 91, 88])

    objects = [obj1, obj2, obj3, obj4]

    # Test with top-k strategy
    list_config = {
        "tags": {"strategy": "top_k", "top_k": 2},
        "scores": {"strategy": "top_k", "top_k": 2},
    }

    concrete_obj = run_self_consistency(
        objects, schema=ModelWithList, config=list_config
    )

    assert isinstance(concrete_obj, ModelWithList)
    assert concrete_obj.name == "Alice"
    # "python" appears 4 times, "ml" appears 3 times - should be top 2
    assert set(concrete_obj.tags) == {"python", "ml"}
    # 85 appears 4 times, 88 appears 3 times - should be top 2
    assert set(concrete_obj.scores) == {85, 88}


def test_self_consistency_with_list_attributes_threshold():
    """Test self-consistency with list attributes using threshold strategy."""
    # Create objects with list attributes
    obj1 = ModelWithList(name="Alice", tags=["python", "ml", "ai"], scores=[85, 90, 88])
    obj2 = ModelWithList(name="Alice", tags=["python", "data", "ml"], scores=[85, 92, 88])
    obj3 = ModelWithList(name="Alice", tags=["python", "ml", "nlp"], scores=[85, 90, 89])
    obj4 = ModelWithList(name="Alice", tags=["python", "ai", "data"], scores=[85, 91, 88])

    objects = [obj1, obj2, obj3, obj4]

    # Test with threshold strategy
    list_config = {
        "tags": {"strategy": "threshold", "threshold": 3.0},  # Items appearing 3+ times
        "scores": {"strategy": "threshold", "threshold": 4.0},  # Items appearing 4+ times
    }

    concrete_obj = run_self_consistency(
        objects, schema=ModelWithList, config=list_config
    )

    assert isinstance(concrete_obj, ModelWithList)
    assert concrete_obj.name == "Alice"
    # "python" appears 4 times, "ml" appears 3 times - should be above threshold
    assert set(concrete_obj.tags) == {"python", "ml"}
    # Only 85 appears 4 times - should be above threshold
    assert set(concrete_obj.scores) == {85}


def test_self_consistency_with_list_attributes_default():
    """Test self-consistency with list attributes using default behavior (top-1)."""
    # Create objects with list attributes
    obj1 = ModelWithList(name="Alice", tags=["python", "ml", "ai"], scores=[85, 90, 88])
    obj2 = ModelWithList(name="Alice", tags=["python", "data", "ml"], scores=[85, 92, 88])
    obj3 = ModelWithList(name="Alice", tags=["python", "ml", "nlp"], scores=[85, 90, 89])
    obj4 = ModelWithList(name="Alice", tags=["python", "ai", "data"], scores=[85, 91, 88])

    objects = [obj1, obj2, obj3, obj4]

    # Test with default behavior (no list_config)
    concrete_obj = run_self_consistency(objects, schema=ModelWithList)

    assert isinstance(concrete_obj, ModelWithList)
    assert concrete_obj.name == "Alice"
    # Should return top-1 item for each list
    assert concrete_obj.tags == ["python"]  # "python" appears most frequently
    assert concrete_obj.scores == [85]  # "85" appears most frequently


def test_list_config_defaults():
    """Test that ListConfig uses appropriate defaults when not specified."""
    # Create objects with list attributes
    obj1 = ModelWithList(name="Alice", tags=["python", "ml", "ai"], scores=[85, 90, 88])
    obj2 = ModelWithList(name="Alice", tags=["python", "data", "ml"], scores=[85, 92, 88])
    obj3 = ModelWithList(name="Alice", tags=["python", "ml", "nlp"], scores=[85, 90, 89])
    obj4 = ModelWithList(name="Alice", tags=["python", "ai", "data"], scores=[85, 91, 88])

    objects = [obj1, obj2, obj3, obj4]

    # Test with minimal configuration - should use defaults
    config = SelfConsistencyConfig(
        list_config={
            "tags": ListConfig(),  # Uses defaults: strategy="top_k", top_k=0
            "scores": ListConfig(strategy="threshold"),  # Uses default threshold=2.0
        }
    )

    concrete_obj = run_self_consistency(
        objects, schema=ModelWithList, config=config
    )

    assert isinstance(concrete_obj, ModelWithList)
    assert concrete_obj.name == "Alice"
    # tags: top_k=0 means use default behavior (top-1)
    assert concrete_obj.tags == ["python"]
    # scores: threshold=2.0 means items appearing 2+ times
    # 85 appears 4 times, 88 appears 3 times, 90 appears 2 times
    assert set(concrete_obj.scores) == {85, 88, 90}
