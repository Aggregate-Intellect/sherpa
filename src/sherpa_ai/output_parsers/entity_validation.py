"""Entity validation module for Sherpa AI.

This module provides functionality for validating named entities in text.
It defines the EntityValidation class which verifies that entities mentioned
in generated text exist in the source material, using various similarity methods.
"""

from enum import Enum
from typing import Tuple

from langchain_core.language_models import BaseLanguageModel

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
    """Methods for comparing text similarity.

    This enum defines the available methods for comparing text similarity
    when validating entities.

    Attributes:
        BASIC (int): Simple text matching.
        METRICS (int): Similarity metrics-based comparison.
        LLM (int): Language model-based comparison.
    """

    BASIC = 0
    METRICS = 1
    LLM = 2


class EntityValidation(BaseOutputProcessor):
    """Validator for named entities in text.

    This class validates that entities mentioned in generated text can be
    found in the source material, using progressively more sophisticated
    similarity comparison methods if initial validation fails.

    Example:
        >>> validator = EntityValidation()
        >>> belief = Belief()  # Contains source text about "John Smith"
        >>> result = validator.process_output("John Smith is CEO.", belief)
        >>> print(result.is_valid)
        True
        >>> result = validator.process_output("Jane Doe is CEO.", belief)
        >>> print(result.is_valid)
        False
    """

    def process_output(
        self, text: str, belief: Belief, llm: BaseLanguageModel = None, **kwargs
    ) -> ValidationResult:
        """Validate entities in text against source material.

        This method checks that entities mentioned in the input text can be
        found in the source material stored in the belief state. It uses
        increasingly sophisticated comparison methods on validation failures.

        Args:
            text (str): Text containing entities to validate.
            belief (Belief): Agent's belief state containing source material.
            llm (BaseLanguageModel, optional): Language model for advanced comparison.
            **kwargs: Additional arguments for processing.

        Returns:
            ValidationResult: Result indicating whether all entities are valid,
                           with feedback if validation fails.

        Example:
            >>> validator = EntityValidation()
            >>> belief = Belief()  # Contains text about "Microsoft"
            >>> result = validator.process_output("Microsoft announced...", belief)
            >>> print(result.is_valid)
            True
            >>> print(result.feedback)
            ''
        """
        source = belief.get_histories_excluding_types(
            exclude_types=["feedback", "result", "action"],
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
        """Select text similarity comparison method.

        This method determines which similarity comparison method to use
        based on the number of previous validation attempts.

        Args:
            value (int): The iteration count value used to determine the text similarity state.
                         0: Use BASIC text similarity.
                         1: Use text similarity BY_METRICS.
                         Default: Use text similarity BY_LLM.

        Returns:
            TextSimilarityMethod: Selected comparison method.

        Example:
            >>> validator = EntityValidation()
            >>> method = validator.similarity_picker(0)
            >>> print(method)
            TextSimilarityMethod.BASIC
            >>> method = validator.similarity_picker(2)
            >>> print(method)
            TextSimilarityMethod.LLM
        """
        switch_dict = {0: TextSimilarityMethod.BASIC, 1: TextSimilarityMethod.METRICS}
        return switch_dict.get(value, TextSimilarityMethod.LLM)

    def get_failure_message(self) -> str:
        """Get a message describing validation failures.

        Returns:
            str: Warning message about potential missing entities.

        Example:
            >>> validator = EntityValidation()
            >>> print(validator.get_failure_message())
            'Some enitities from the source might not be mentioned.'
        """
        return "Some enitities from the source might not be mentioned."

    def check_entities_match(
        self,
        result: str,
        source: str,
        stage: TextSimilarityMethod,
        llm: BaseLanguageModel,
    ):
        """Check if entities in result match those in source.

        This method compares entities between result and source text using
        the specified similarity comparison method.

        Args:
            result (str): Text containing entities to validate.
            source (str): Source text to validate against.
            stage (TextSimilarityMethod): Comparison method to use.
            llm (BaseLanguageModel): Language model for LLM-based comparison.

        Returns:
            Tuple[bool, str]: Whether entities match and error message if not.

        Example:
            >>> validator = EntityValidation()
            >>> match, msg = validator.check_entities_match(
            ...     "Apple released...",
            ...     "Apple announced...",
            ...     TextSimilarityMethod.BASIC,
            ...     None
            ... )
            >>> print(match)
            True
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
