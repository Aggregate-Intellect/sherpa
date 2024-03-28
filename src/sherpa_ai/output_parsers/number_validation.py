from typing import Tuple

from sherpa_ai.events import EventType
from sherpa_ai.memory import Belief
from sherpa_ai.output_parsers.base import BaseOutputProcessor
from sherpa_ai.output_parsers.validation_result import ValidationResult
from sherpa_ai.utils import verify_numbers_against_source


class NumberValidation(BaseOutputProcessor):
    """
    Process and validate numerical information in the generated text.

    This class inherits from the BaseOutputProcessor and provides a method to process
    the generated text and validate the presence of numerical information based on a
    specified source.

    Methods:
    - process_output(text: str) -> ValidationResult:
        Process the generated text and validate the presence of numerical information.

    Example Usage:
    ```python
    number_validator = NumberValidation(source="document")
    result = number_validator.process_output("The document contains important numbers: 123, 456.")
    ```

    """

    def process_output(self, text: str, belief: Belief) -> ValidationResult:
        """
        Verifies that all numbers within `text` exist in the `belief` source text.
        Args:
            text: The text to be processed
            belief: The belief object of the agent that generated the output
        Returns:
            ValidationResult: The result of the validation. If any number in the
            text to be processed doesn't exist in the source text,
            validation is invalid and contains a feedback string.
            Otherwise validation is valid.
        """
        source = belief.get_histories_excluding_types(
            exclude_types=[EventType.feedback, EventType.result],
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
            return ValidationResult(
                is_valid=False,
                result=text,
                feedback=error_message,
            )

    def get_failure_message(self) -> str:
        return "The numeric value results might not be fully reliable. Exercise caution and consider alternative sources if possible."
