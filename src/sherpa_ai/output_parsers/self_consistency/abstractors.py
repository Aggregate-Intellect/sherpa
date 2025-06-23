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
    def abstract(self, values: list) -> DiscreteDistribution:
        """
        Abstract the values into a discrete distribution based on the counts of each unique value.
        TODO: Support custom equality functions or equality matrix

        Args:
            values: A list of values to abstract.

        Returns:
            A DiscreteDistribution object representing the counts of each unique value.
        """  # noqa: E501
        if not values:
            raise ValueError("The input list cannot be empty.")

        counter = Counter(values)
        unique_values = list(counter.keys())
        probabilities = [counter[value] / len(values) for value in unique_values]
        return DiscreteDistribution(unique_values, probabilities)
