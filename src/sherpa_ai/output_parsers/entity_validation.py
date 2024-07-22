from enum import Enum
from typing import Tuple

from langchain_core.language_models import BaseLanguageModel 

from sherpa_ai.events import EventType
from sherpa_ai.memory import Belief
from sherpa_ai.output_parsers.base import BaseOutputProcessor
from sherpa_ai.output_parsers.validation_result import ValidationResult
from sherpa_ai.utils import (
    extract_entities,
    text_similarity,
    text_similarity_by_llm,
    text_similarity_by_metrics,
)


class TextSimilarityMethod(Enum):
    BASIC = 0
    METRICS = 1
    LLM = 2


class EntityValidation(BaseOutputProcessor):
    """
     Process and validate the presence of entities in the generated text.

    This class inherits from the BaseOutputProcessor and provides a method to process
    the generated text and validate the presence of entities based on a specified source.

    Methods:
    - process_output(text: str, belief: Belief) -> ValidationResult:
        Process the generated text and validate the presence of entities.

    - get_failure_message() -> str:
        Returns a failure message to be displayed when the validation fails.

    """

    def process_output(
        self, text: str, belief: Belief, llm: BaseLanguageModel = None, **kwargs
    ) -> ValidationResult:
        """
        Verifies that entities within `text` exist in the `belief` source text.
        Args:
            text: The text to be processed
            belief: The belief object of the agent that generated the output
            iteration_count (int, optional): The iteration count for validation processing.
                    1. means basic text similarity.
                    2  means text similarity by metrics.
                    3 means text similarity by llm.
        Returns:
            ValidationResult: The result of the validation. If any entity in the
            text to be processed doesn't exist in the source text,
            validation is invalid and contains a feedback string.
            Otherwise, validation is valid.
        """

        source = belief.get_histories_excluding_types(
            exclude_types=[EventType.feedback, EventType.result, EventType.action],
        )
        entity_exist_in_source, error_message = self.check_entities_match(
            text, source, self.similarity_picker(self.count), llm
        )
        if entity_exist_in_source:
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

    def similarity_picker(self, value: int):
        """
        Picks a text similarity state based on the provided iteration count value.

        Args:
            value (int): The iteration count value used to determine the text similarity state.
                        - 0: Use BASIC text similarity.
                        - 1: Use text similarity BY_METRICS.
                        - Default: Use text similarity BY_LLM.

        Returns:
            TextSimilarityState: The selected text similarity state.
        """
        switch_dict = {0: TextSimilarityMethod.BASIC, 1: TextSimilarityMethod.METRICS}
        return switch_dict.get(value, TextSimilarityMethod.LLM)

    def get_failure_message(self) -> str:
        return "Some enitities from the source might not be mentioned."

    def check_entities_match(
        self,
        result: str,
        source: str,
        stage: TextSimilarityMethod,
        llm: BaseLanguageModel,
    ):
        """
        Check if entities extracted from a question are present in an answer.

        Args:
        - result (str): Answer text.
        - source (str): Question text.
        - stage (int): Stage of the check (0, 1, or 2).

        Returns:
        dict: Result of the check containing
        """

        stage = stage.value
        source_entity = extract_entities(source)
        check_entity = extract_entities(result)
        if stage == 0:
            return text_similarity(
                check_entity=check_entity, source_entity=source_entity
            )
        elif stage == 1:
            return text_similarity_by_metrics(
                check_entity=check_entity, source_entity=source_entity
            )
        elif stage > 1 and llm is not None:
            return text_similarity_by_llm(
                llm=llm,
                source_entity=source_entity,
                result=result,
                source=source,
            )
        return text_similarity_by_metrics(
            check_entity=check_entity, source_entity=source_entity
        )
