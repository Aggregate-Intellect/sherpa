from typing import Tuple

from sherpa_ai.events import EventType
from sherpa_ai.memory import Belief
from sherpa_ai.output_parsers.base import BaseOutputProcessor
from sherpa_ai.output_parsers.validation_result import ValidationResult
from sherpa_ai.utils import check_if_number_exist


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
        Process the output to check if the number exists in the source
        Args:
            text: The text to be processed
            belief: The belief object of the agent generated the output
        Returns:
            ValidationResult: The result of the validation, it is not valid if the
            number does not exist in the source while a feedback will be given
        """
        source = belief.get_histories_excluding_types(
            exclude_type=[EventType.feedback, EventType.result],
        )
        check_validation = check_if_number_exist(text, source)
        if check_validation["number_exists"]:
            return ValidationResult(
                is_valid=True,
                result=text,
                feedback="",
            )
        else:
            return ValidationResult(
                is_valid=False,
                result=text,
                feedback=check_validation["messages"],
            )

    def get_failure_message(self) -> str:
        return "The numeric value results might not be fully reliable. Exercise caution and consider alternative sources if possible."
