from abc import ABC, abstractmethod
from typing import Any, List


class Distribution(ABC):
    @abstractmethod
    def get_probability(self, value) -> float:
        """
        Get the probability of a value in the distribution.

        Args:
            value: The value to get the probability for.
        Returns:
            The probability of the value.
        Raises:
            ValueError: If the value is not in the distribution.
        """
        pass

    @abstractmethod
    def get_mode(self) -> Any:
        """
        Get the mode of the distribution, which is the value with the highest probability.
        Returns:
            The mode of the distribution.
        """  # noqa: E501
        pass


class DiscreteDistribution(Distribution):
    def __init__(self, values: list, probabilities: list[float]):
        if len(values) != len(probabilities):
            raise ValueError("Values and probabilities must have the same length.")
        if not all(0 <= p <= 1 for p in probabilities):
            raise ValueError("Probabilities must be between 0 and 1.")
        if not abs(sum(probabilities) - 1) < 1e-6:
            raise ValueError("Probabilities must sum to 1.")

        self.values = values
        self.probabilities = {
            self.values[i]: probabilities[i] for i in range(len(probabilities))
        }

    def get_probability(self, value) -> float:
        if value not in self.probabilities:
            raise ValueError(f"Value {value} not in distribution.")
        return self.probabilities.get(value)

    def get_mode(self) -> Any:
        max_item = max(self.probabilities.items(), key=lambda x: x[1])
        return max_item[0]


class CountDistribution(Distribution):
    """
    A distribution that represents counts of values without requiring normalization.
    This is useful for list attributes where we want to count occurrences.
    """
    
    def __init__(self, values: list, counts: list[float]):
        if len(values) != len(counts):
            raise ValueError("Values and counts must have the same length.")
        if not all(count >= 0 for count in counts):
            raise ValueError("Counts must be non-negative.")

        self.values = values
        self.counts = {
            self.values[i]: counts[i] for i in range(len(counts))
        }

    def get_probability(self, value) -> float:
        if value not in self.counts:
            raise ValueError(f"Value {value} not in distribution.")
        total = sum(self.counts.values())
        return self.counts.get(value) / total if total > 0 else 0.0

    def get_mode(self) -> Any:
        max_item = max(self.counts.items(), key=lambda x: x[1])
        return max_item[0]
    
    def get_top_k(self, k: int) -> List[Any]:
        """
        Get the top-k values with highest counts.
        
        Args:
            k: Number of top values to return
            
        Returns:
            List of top-k values sorted by count (descending)
        """
        sorted_items = sorted(self.counts.items(), key=lambda x: x[1], reverse=True)
        return [item[0] for item in sorted_items[:k]]
    
    def get_above_threshold(self, threshold: float) -> List[Any]:
        """
        Get all values with counts above the specified threshold.
        
        Args:
            threshold: Minimum count threshold
            
        Returns:
            List of values with counts above threshold, sorted by count (descending)
        """
        above_threshold = [(value, count) for value, count in self.counts.items() if count >= threshold]
        sorted_items = sorted(above_threshold, key=lambda x: x[1], reverse=True)
        return [item[0] for item in sorted_items]
