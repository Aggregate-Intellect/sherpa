from typing import Tuple

from sherpa_ai.memory import Belief
from sherpa_ai.output_parsers.base import BaseOutputParser, BaseOutputProcessor
from sherpa_ai.utils import check_entities_match
from sherpa_ai.output_parsers.citation_validation import CitationValidation


class EntityValidation(BaseOutputProcessor):
    def __init__(self, source: str, stage: int):
        self.stage = stage
        self.source = source

    def process_output(self, text: str) -> Tuple[bool, str]:
        check_validation = check_entities_match(text, self.source, self.stage)
        print('----------------------------------------' , flush=True)
        print(check_validation, flush=True)
        print('----------------------------------------', flush=True)
        if check_validation["entity_exist"] == True:
            return True, text
        else:
            return False, check_validation["messages"]
