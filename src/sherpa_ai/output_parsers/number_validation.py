from typing import Tuple

from sherpa_ai.memory import Belief
from sherpa_ai.output_parsers.base import BaseOutputProcessor
from sherpa_ai.utils import check_if_number_exist


class NumberValidation(BaseOutputProcessor):
    def __init__(
        self,
        source: str,
    ):
        # threshold

        self.source = source
    def process_output(self, text: str) -> Tuple[bool, str]:
        check_validation = check_if_number_exist( text ,self.source)
        if check_validation['number_exists']==True:
            return True, text
        else:
            return False , check_validation['messages']
