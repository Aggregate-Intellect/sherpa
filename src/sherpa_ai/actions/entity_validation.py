from enum import Enum
from typing import Any

from sherpa_ai.actions.base import BaseAction
from sherpa_ai.events import EventType
from sherpa_ai.memory.belief import Belief
from sherpa_ai.memory.shared_memory import SharedMemory
from sherpa_ai.tools import SearchArxivTool
from langchain_core.language_models import BaseLanguageModel
from sherpa_ai.output_parsers.validation_result import ValidationResult
from loguru import logger
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


class EntityValidationAction(BaseAction):
    llm: Any  # The BaseLanguageModel from LangChain is not compatible with Pydantic 2 yet
    belief: Any = None

    # Override the name and args from BaseAction
    name: str = "Entity Validator"
    args: dict = {
        "target_text": "the value to validate.",
        "source_text": "the value to compare against. where the answer generated from",
    }
    usage: str = (
        "simple entity validation that checks if entities in the target_text exist in the source_text text."
    )

    count: int = 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def execute(self, target_text: str, source_text: str, **kwargs) -> str:
        """
        Verifies that entities within `text` exist in the `source` text.
        Args:
            target_text: The text to be processed
            source_text: The source text to compare against
            iteration_count (int, optional): The iteration count for validation processing.
                1 means basic text similarity.
                2 means text similarity by metrics.
                3 means text similarity by llm.
        Returns:
            ValidationResult: The result of the validation. If any entity in the
            text to be processed doesn't exist in the source text,
            validation is invalid and contains a feedback string.
            Otherwise, validation is valid.
        """
        source = self.belief.get_histories_excluding_types(
            exclude_types=[EventType.feedback, EventType.result, EventType.action],
        )   

        if not source:
            source = source_text
        logger.info(f"Entity Validation Action: {self.name}")
        logger.info(f"Text: {target_text}")
        logger.info(f"Source: {source}")
        entity_exist_in_source, error_message = self.check_entities_match(
            target_text, source, self.similarity_picker(self.count), self.llm
        )
        if entity_exist_in_source:
            return str(
                ValidationResult(
                    is_valid=True,
                    result=target_text,
                    feedback="",
                )
            )
        else:
            self.count += 1
            return str(
                ValidationResult(
                    is_valid=True,
                    result=target_text,
                    feedback="",
                )
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
        return "Some entities from the source might not be mentioned."

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
