from pydantic import BaseModel

from sherpa_ai.output_parsers.self_consistency.abstract_objects import AbstractObject
from sherpa_ai.output_parsers.self_consistency.concretizer import (
    MaximumLikelihoodConcretizer,
)
from sherpa_ai.output_parsers.self_consistency.distributions import DiscreteDistribution


class TestModel(BaseModel):
    """Test model for concretizer testing"""

    name: str
    age: int
    active: bool


class NestedTestModel(BaseModel):
    """Nested test model for concretizer testing"""

    user: TestModel
    score: float
    tag: str


class TestMaximumLikelihoodConcretizer:
    """Test cases for MaximumLikelihoodConcretizer"""

    def setup_method(self):
        """Set up test fixtures"""
        self.concretizer = MaximumLikelihoodConcretizer()

    def test_concretize_with_distributions_returns_model(self):
        """Test concretizing abstract object with distributions returns BaseModel"""
        # Create distributions
        name_dist = DiscreteDistribution(
            values=["Alice", "Bob", "Charlie"], probabilities=[0.5, 0.3, 0.2]
        )
        age_dist = DiscreteDistribution(
            values=[25, 30, 35], probabilities=[0.2, 0.6, 0.2]
        )
        active_dist = DiscreteDistribution(
            values=[True, False], probabilities=[0.8, 0.2]
        )

        # Create abstract object
        obj_dict = {"name": name_dist, "age": age_dist, "active": active_dist}
        abstract_obj = AbstractObject(obj_schema=TestModel, obj_dict=obj_dict)

        # Concretize
        result = self.concretizer.concretize(abstract_obj, return_dict=False)

        # Assertions
        assert isinstance(result, TestModel)
        assert result.name == "Alice"  # Most likely value (0.5 probability)
        assert result.age == 30  # Most likely value (0.6 probability)
        assert result.active is True  # Most likely value (0.8 probability)

    def test_concretize_with_distributions_returns_dict(self):
        """Test concretizing an abstract object with distributions returns a dict"""
        # Create distributions
        name_dist = DiscreteDistribution(
            values=["Alice", "Bob"], probabilities=[0.7, 0.3]
        )
        age_dist = DiscreteDistribution(values=[25, 30], probabilities=[0.4, 0.6])
        active_dist = DiscreteDistribution(
            values=[True, False], probabilities=[0.9, 0.1]
        )

        # Create abstract object
        obj_dict = {"name": name_dist, "age": age_dist, "active": active_dist}
        abstract_obj = AbstractObject(obj_schema=TestModel, obj_dict=obj_dict)

        # Concretize with return_dict=True
        result = self.concretizer.concretize(abstract_obj, return_dict=True)

        # Assertions
        assert isinstance(result, dict)
        assert result["name"] == "Alice"  # Most likely value (0.7 probability)
        assert result["age"] == 30  # Most likely value (0.6 probability)
        assert result["active"] is True  # Most likely value (0.9 probability)

    def test_concretize_nested_object_with_distributions(self):
        """Test concretizing a nested object with distributions"""
        # Create distributions for nested object
        name_dist = DiscreteDistribution(
            values=["Alice", "Bob"], probabilities=[0.6, 0.4]
        )
        age_dist = DiscreteDistribution(values=[25, 30], probabilities=[0.3, 0.7])
        score_dist = DiscreteDistribution(
            values=[95.5, 87.2, 92.1], probabilities=[0.5, 0.2, 0.3]
        )
        active_dist = DiscreteDistribution(
            values=[True, False], probabilities=[0.8, 0.2]
        )

        tag_dist = DiscreteDistribution(
            values=["important", "verified"],
            probabilities=[0.7, 0.3],
        )

        # Create nested abstract object
        obj_dict = {
            "user": {"name": name_dist, "age": age_dist, "active": active_dist},
            "score": score_dist,
            "tag": tag_dist,
        }
        abstract_obj = AbstractObject(obj_schema=NestedTestModel, obj_dict=obj_dict)

        # Concretize
        result = self.concretizer.concretize(abstract_obj, return_dict=False)

        # Assertions
        assert isinstance(result, NestedTestModel)
        assert isinstance(result.user, TestModel)
        assert result.user.name == "Alice"  # Mode of name distribution
        assert result.user.age == 30  # Mode of age distribution
        assert result.user.active is True  # Unchanged value
        assert result.score == 95.5  # Mode of score distribution
        assert result.tag == "important"  # Unchanged value
