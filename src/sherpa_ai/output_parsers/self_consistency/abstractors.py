from abc import ABC, abstractmethod
from collections import Counter

from sherpa_ai.output_parsers.self_consistency.distributions import (
    DiscreteDistribution,
    Distribution,
)


class AttributeAbstractor(ABC):
    @abstractmethod
    def abstract(self, values: list) -> Distribution:
        """
        Abstract the values into a distribution.
        This method should be implemented by subclasses.

        Args:
            values: A list of values to abstract.

        Returns:
            A Distribution object representing the abstracted values.
        """
        pass


class CountingAttributeAbstractor:
    def abstract(self, values: list, weights: dict = {}) -> DiscreteDistribution:
        """
        Abstract the values into a discrete distribution based on the counts of each unique value.
        TODO: Support custom equality functions or equality matrix

        Args:
            values: A list of values to abstract.
            weights: A dictionary mapping each value to its weight. The default weight is 1.0.

        Returns:
            A DiscreteDistribution object representing the counts of each unique value.
        """  # noqa: E501
        if not values:
            raise ValueError("The input list cannot be empty.")

        counter = Counter(values)
        unique_values = list(counter.keys())
        values = [weights.get(value, 1.0) * counter[value] for value in unique_values]
        total_count = sum(values)
        probabilities = [count / total_count for count in values]

        return DiscreteDistribution(unique_values, probabilities)
