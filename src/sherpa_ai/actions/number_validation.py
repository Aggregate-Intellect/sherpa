from enum import Enum
from typing import Any, List

from sherpa_ai.actions.base import BaseAction
from sherpa_ai.events import EventType
from sherpa_ai.memory.belief import Belief
from loguru import logger
from sherpa_ai.output_parsers.validation_result import ValidationResult
from sherpa_ai.utils import (
    verify_numbers_against_source,
)


class NumberValidationAction(BaseAction):

    name: str = "Number validator"
    args: dict = {
        "target_text": "the value to validate.",
        "source_text": "the value to compare against. where the answer generated from",
    }
    usage: str = (
        "simple number citation validation that checks if number in the target_text exist in the source_text text."
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def execute(self, target_text: str, source_text: str, **kwargs) -> str:
        """
        Verifies that all numbers within `text` exist in the `belief` source text.

        Args:
            text: The text to be analyzed
            belief: Belief of the Agent that generated `text`
        Returns:
            ValidationResult: The result of number validation. If any number in the
            text to be processed doesn't exist in the source text,
            validation is invalid and contains a feedback string.
            Otherwise validation is valid.
        """

        source = self.belief.get_histories_excluding_types(
            exclude_types=[EventType.feedback, EventType.result],
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
