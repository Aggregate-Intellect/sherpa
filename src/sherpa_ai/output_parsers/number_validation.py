from typing import Tuple

from sherpa_ai.memory import Belief
from sherpa_ai.output_parsers.base import BaseOutputProcessor
from sherpa_ai.output_parsers.validation_result import ValidationResult
from sherpa_ai.utils import check_if_number_exist


class NumberValidation(BaseOutputProcessor):
    def __init__(
        self,
        source: str,
    ):
        self.source = source

    def process_output(self, text: str) -> ValidationResult:
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
