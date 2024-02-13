from typing import Tuple

from sherpa_ai.memory import Belief
from sherpa_ai.output_parsers.base import BaseOutputProcessor
from sherpa_ai.utils import check_entities_match
from sherpa_ai.output_parsers.citation_validation import CitationValidation


class EntityValidation(BaseOutputProcessor):
    def __init__(self, source: str, stage: int):
        self.stage = stage
        self.source = source

    def process_output(self, text: str) -> Tuple[bool, str]:
        check_validation = check_entities_match(text, self.source, self.stage)

        print("-------  - - - - - this is inside the thing - ---- - -- -------------")

        print(self.source)
        print(text)
        print(check_validation)
        print(self.stage)

        print(" -------------------------- JAKARAND MINAMIN ------------------------")

        if check_validation["entity_exisist"] == True:
            return True, text
        else:
            return False, check_validation["messages"]
