from enum import Enum
from typing import Any, List

from loguru import logger

from sherpa_ai.actions.base import BaseAction
from sherpa_ai.memory.belief import Belief
from sherpa_ai.output_parsers.validation_result import ValidationResult
from sherpa_ai.utils import verify_numbers_against_source


class NumberValidationAction(BaseAction):
    """An action for validating numbers in text against a source.
    
    This class provides functionality to verify that numbers extracted from a target
    text exist in a source text, ensuring numerical accuracy in generated content.
    
    This class inherits from :class:`BaseAction` and provides methods to:
      - Validate numbers in text against a source
      - Extract and verify numerical values
      - Provide feedback on validation results
    
    Attributes:
        name (str): Name of the action, set to "Number validator".
        args (dict): Arguments required by the action.
        usage (str): Description of the action's usage.
    
    Example:
        >>> validator = NumberValidationAction()
        >>> result = validator.execute(
        ...     target_text="The population is 8.9 million",
        ...     source_text="The city has a population of 8.9 million people"
        ... )
        >>> print(result)
        {"is_valid": true, "result": "The population is 8.9 million", "feedback": ""}
    """

    name: str = "Number validator"
    args: dict = {
        "target_text": "the value to validate.",
        "source_text": "the value to compare against. where the answer generated from",
    }
    usage: str = (
        "simple number citation validation that checks if number in the target_text exist in the source_text text."
    )

    def __init__(self, **kwargs):
        """Initialize a NumberValidationAction with the provided parameters.
        
        Args:
            **kwargs: Keyword arguments passed to the parent class.
        """
        super().__init__(**kwargs)

    def execute(self, target_text: str, source_text: str, **kwargs) -> str:
        """Verify that all numbers within the target text exist in the source text.
        
        This method extracts numbers from both texts and compares them to ensure
        that all numerical values in the target text are present in the source text.
        
        Args:
            target_text (str): The text to be validated.
            source_text (str): The source text to compare against.
            **kwargs: Additional keyword arguments.
            
        Returns:
            str: A string of the result of number validation. If any number in the
            text to be processed doesn't exist in the source text,
            validation is invalid and contains a feedback string.
            Otherwise validation is valid.
        """
        source = self.belief.get_histories_excluding_types(
            exclude_types=["feedback", "result"],
        )

        if not source:
            source = source_text

        logger.info(f"Number Validation Action: {self.name}")
        logger.info(f"Text: {target_text}")
        logger.info(f"Source: {source}")

        numbers_exist_in_source, error_message = verify_numbers_against_source(
            target_text, source
        )

        if numbers_exist_in_source:
            return str(
                ValidationResult(
                    is_valid=True,
                    result=target_text,
                    feedback="",
                )
            )
        else:
            return str(
                ValidationResult(
                    is_valid=False,
                    result=target_text,
                    feedback=error_message,
                )
            )
