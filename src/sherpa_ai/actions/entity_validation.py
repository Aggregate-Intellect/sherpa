from enum import Enum
from typing import Any

from langchain_core.language_models import BaseLanguageModel
from loguru import logger

from sherpa_ai.actions.base import BaseAction
from sherpa_ai.output_parsers.validation_result import ValidationResult
from sherpa_ai.utils import (
    extract_entities,
    text_similarity,
    text_similarity_by_llm,
    text_similarity_by_metrics,
)


class TextSimilarityMethod(Enum):
    """Enumeration of text similarity comparison methods.
    
    This enum defines the different methods available for comparing text similarity,
    with increasing levels of sophistication.
    
    Attributes:
        BASIC (int): Basic text similarity comparison using simple matching.
        METRICS (int): Text similarity comparison using various metrics.
        LLM (int): Text similarity comparison using a language model.
    
    Example:
        >>> method = TextSimilarityMethod.BASIC
        >>> print(method.value)
        0
    """
    BASIC = 0
    METRICS = 1
    LLM = 2


class EntityValidationAction(BaseAction):
    """An action for validating entities in text against a source.
    
    This class provides functionality to verify that entities extracted from a target
    text exist in a source text, using various similarity comparison methods.
    
    This class inherits from :class:`BaseAction` and provides methods to:
      - Validate entities in text against a source
      - Compare text similarity using different methods
      - Extract and check entities for matches
    
    Attributes:
        llm (Any): Language model used for advanced text similarity comparison.
        belief (Any): Belief system for storing and retrieving information.
        name (str): Name of the action, set to "Entity Validator".
        args (dict): Arguments required by the action.
        usage (str): Description of the action's usage.
        count (int): Counter for tracking validation iterations.
    
    Example:
        >>> validator = EntityValidationAction(llm=my_llm)
        >>> result = validator.execute(
        ...     target_text="The capital of France is Paris",
        ...     source_text="Paris is the capital city of France"
        ... )
        >>> print(result)
        {"is_valid": true, "result": "The capital of France is Paris", "feedback": ""}
    """
    
    llm: Any  # The BaseLanguageModel from LangChain is not compatible with Pydantic 2 yet
    belief: Any = None

    # Override the name and args from BaseAction
    name: str = "Entity Validator"
    args: dict = {
        "target_text": "the value to validate.",
        "source_text": "the value to compare against. where the answer generated from",
    }
    usage: str = "simple entity validation that checks if entities in the target_text exist in the source_text text."

    count: int = 0

    def __init__(self, **kwargs):
        """Initialize an EntityValidationAction with the provided parameters.
        
        Args:
            **kwargs: Keyword arguments passed to the parent class.
        """
        super().__init__(**kwargs)

    def execute(self, target_text: str, source_text: str, **kwargs) -> str:
        """Verify that entities within the target text exist in the source text.
        
        This method extracts entities from both texts and compares them using
        different similarity methods based on the iteration count.
        
        Args:
            target_text (str): The text to be validated.
            source_text (str): The source text to compare against.
            **kwargs: Additional keyword arguments.
            
        Returns:
            str: A string representation of a ValidationResult object.
        """
        source = self.belief.get_histories_excluding_types(
            exclude_types=["feedback", "result", "action"],
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

    def similarity_picker(self, value: int) -> TextSimilarityMethod:
        """Select a text similarity method based on the iteration count.
        
        This method determines which similarity comparison method to use based
        on the current iteration count.
        
        Args:
            value (int): The iteration count value.
                0: Use BASIC text similarity.
                1: Use text similarity BY_METRICS.
                Default: Use text similarity BY_LLM.
            
        Returns:
            TextSimilarityMethod: The selected text similarity method.
        """
        switch_dict = {0: TextSimilarityMethod.BASIC, 1: TextSimilarityMethod.METRICS}
        return switch_dict.get(value, TextSimilarityMethod.LLM)

    def get_failure_message(self) -> str:
        """Return a standard failure message for entity validation.
        
        Returns:
            str: A message indicating that some entities might not be mentioned.
        """
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
            result (str): The text to check for entities.
            source (str): The source text to compare against.
            stage (TextSimilarityMethod): The similarity method to use.
            llm (BaseLanguageModel): Language model for LLM-based comparison.
            
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
