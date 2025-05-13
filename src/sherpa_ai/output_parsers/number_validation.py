"""Number validation module for Sherpa AI.

This module provides functionality for validating numerical information in text.
It defines the NumberValidation class which verifies that numbers mentioned in
generated text exist in the source material.
"""

from typing import Tuple

from loguru import logger

from sherpa_ai.memory import Belief
from sherpa_ai.output_parsers.base import BaseOutputProcessor
from sherpa_ai.output_parsers.validation_result import ValidationResult
from sherpa_ai.utils import verify_numbers_against_source


class NumberValidation(BaseOutputProcessor):
    """
    Validates the presence or absence of numerical information in a given piece of text.

    This class validates that any numbers mentioned in generated text can be
    found in the source material, helping ensure numerical accuracy and prevent
    hallucination of numbers.

    Example:
        >>> validator = NumberValidation()
        >>> belief = Belief()  # Contains source text with "42 items"
        >>> result = validator.process_output("There are 42 items.", belief)
        >>> print(result.is_valid)
        True
        >>> result = validator.process_output("There are 100 items.", belief)
        >>> print(result.is_valid)
        False
    """

    def process_output(self, text: str, belief: Belief, **kwargs) -> ValidationResult:
        """
        Verifies that all numbers within `text` exist in the `belief` source text.

        Args:
            text (str): Text containing numbers to validate.
            belief (Belief): Agent's belief state containing source material.
            **kwargs: Additional arguments for processing.

        Returns:
            ValidationResult: Result indicating whether all numbers are valid,
                           with feedback if validation fails.

        Example:
            >>> validator = NumberValidation()
            >>> belief = Belief()  # Contains "The price is $50"
            >>> result = validator.process_output("It costs $50", belief)
            >>> print(result.is_valid)
            True
            >>> print(result.feedback)
            ''
        """
        source = belief.get_histories_excluding_types(
            exclude_types=["feedback", "result"],
        )

        numbers_exist_in_source, error_message = verify_numbers_against_source(
            text, source
        )

        if numbers_exist_in_source:
            return ValidationResult(
                is_valid=True,
                result=text,
                feedback="",
            )
        else:
            self.count += 1
            return ValidationResult(
                is_valid=False,
                result=text,
                feedback=error_message,
            )

    def get_failure_message(self) -> str:
        """Get a message describing validation failures.

        Returns:
            str: Warning message about potential numerical inaccuracies.

        Example:
            >>> validator = NumberValidation()
            >>> print(validator.get_failure_message())
            'The numeric value results might not be fully reliable...'
        """
        return "The numeric value results might not be fully reliable. Exercise caution and consider alternative sources if possible."
