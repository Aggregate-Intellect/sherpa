from abc import ABC, abstractmethod
from collections import Counter
from typing import List, Any

from sherpa_ai.output_parsers.self_consistency.distributions import (
    DiscreteDistribution,
    CountDistribution,
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
    def abstract(self, values: list, weights: dict = {}) -> Distribution:
        """
        Abstract the values into a distribution based on the counts of each unique value.
        For list attributes, flattens the list and counts individual elements.
        TODO: Support custom equality functions or equality matrix

        Args:
            values: A list of values to abstract. Can contain lists or primitive values.
            weights: A dictionary mapping each value to its weight. The default weight is 1.0.

        Returns:
            A Distribution object representing the counts of each unique value.
        """  # noqa: E501
        if not values:
            raise ValueError("The input list cannot be empty.")

        # Check if this is a list of lists (list attribute)
        if values and isinstance(values[0], list):
            # Flatten the list of lists
            flattened_values = []
            for sublist in values:
                if isinstance(sublist, list):
                    flattened_values.extend(sublist)
                else:
                    flattened_values.append(sublist)
            
            # Use CountDistribution for list attributes (no normalization constraint)
            counter = Counter(flattened_values)
            unique_values = list(counter.keys())
            counts = [weights.get(value, 1.0) * counter[value] for value in unique_values]
            
            return CountDistribution(unique_values, counts)
        else:
            # Handle primitive values as before
            counter = Counter(values)
            unique_values = list(counter.keys())
            weighted_counts = [weights.get(value, 1.0) * counter[value] for value in unique_values]
            total_count = sum(weighted_counts)
            probabilities = [count / total_count for count in weighted_counts]

            return DiscreteDistribution(unique_values, probabilities)
