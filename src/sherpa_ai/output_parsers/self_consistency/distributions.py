from abc import ABC, abstractmethod


class Distribution(ABC):
    @abstractmethod
    def get_probability(self, value):
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
    def get_mode(self):
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

    def get_probability(self, value):
        if value not in self.probabilities:
            raise ValueError(f"Value {value} not in distribution.")
        return self.probabilities.get(value)

    def get_mode(self):
        max_item = max(self.probabilities.items(), key=lambda x: x[1])
        return max_item[0]
