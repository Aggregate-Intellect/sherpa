from typing import Tuple

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

    Attributes:
    - source (str): The source or context against which numerical information is validated.

    Methods:
    - process_output(text: str) -> ValidationResult:
        Process the generated text and validate the presence of numerical information.

    Example Usage:
    ```python
    number_validator = NumberValidation(source="document")
    result = number_validator.process_output("The document contains important numbers: 123, 456.")
    ```

    """

    def __init__(
        self,
        source: str,
    ):
        """
        Initialize the NumberValidation object.

        Args:
        - source (str): The source or context against which numerical information is validated.
        """
        self.source = source

    def process_output(self, text: str) -> ValidationResult:
        """
        Process the generated text and validate the presence of numerical information.

        Args:
        - text (str): The generated text to be processed.

        Returns:
        - ValidationResult: An object containing the result of the numerical validation,
          including the validity status, the processed text, and optional feedback.

        Example Usage:
        ```python
        result = number_validator.process_output("The document contains important numbers: 123, 456.")
        ```
        """
        check_validation = check_if_number_exist(text, self.source)
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
