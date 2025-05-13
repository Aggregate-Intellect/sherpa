"""Base classes for output parsing and processing in Sherpa AI.

This module provides abstract base classes for output parsing and processing.
It defines the core interfaces that all parsers and processors must implement,
ensuring consistent behavior across different implementations.
"""

from abc import ABC, abstractmethod
from typing import Tuple

from sherpa_ai.output_parsers.validation_result import ValidationResult


class BaseOutputParser(ABC):
    """Abstract base class for output parsers.

    This class defines the interface that all output parsers must implement.
    Output parsers are responsible for transforming raw text output into
    a structured or modified format.

    Example:
        >>> class MyParser(BaseOutputParser):
        ...     def parse_output(self, text: str) -> str:
        ...         return text.upper()
        >>> parser = MyParser()
        >>> result = parser.parse_output("hello")
        >>> print(result)
        'HELLO'
    """

    @abstractmethod
    def parse_output(text: str, **kwargs) -> str:
        """
        Abstract method to be implemented by subclasses for parsing output text.

        Args:
            text (str): The input text to be parsed.
            **kwargs: Additional arguments for parsing.

        Returns:
            str: The parsed output text.

        Example:
            >>> parser = MyParser()
            >>> result = parser.parse_output("hello world")
            >>> print(result)
            'HELLO WORLD'
        """
        pass


class BaseOutputProcessor(ABC):
    """Abstract base class for output processors.

    This class defines the interface that all output processors must implement.
    Output processors validate and transform text output, tracking validation
    failures and providing detailed feedback.

    Attributes:
        count (int): Number of failed validations since last reset.

    Example:
        >>> class MyProcessor(BaseOutputProcessor):
        ...     def process_output(self, text: str) -> ValidationResult:
        ...         valid = len(text) > 5
        ...         return ValidationResult(valid, text, "Length check")
        >>> processor = MyProcessor()
        >>> result = processor("hello world")
        >>> print(result.valid)
        True
    """

    count: int = 0

    def reset_state(self):
        """Reset the validation failure counter.

        This method resets the count of failed validations back to zero.

        Example:
            >>> processor = MyProcessor()
            >>> processor.count = 5
            >>> processor.reset_state()
            >>> print(processor.count)
            0
        """
        self.count = 0

    @abstractmethod
    def process_output(self, text: str, **kwargs) -> ValidationResult:
        """Process and validate the input text.

        Args:
            text (str): The input text to be processed.
            **kwargs: Additional arguments for processing.

        Returns:
            ValidationResult: Result containing validity status, processed text,
                           and optional feedback.

        Example:
            >>> processor = MyProcessor()
            >>> result = processor.process_output("hello world")
            >>> print(result.valid)
            True
            >>> print(result.feedback)
            'Length check'
        """
        pass

    def __call__(self, text: str, **kwargs) -> ValidationResult:
        """Process text using the process_output method.

        This method provides a convenient way to call process_output directly
        on the processor instance.

        Args:
            text (str): The input text to be processed.
            **kwargs: Additional arguments for processing.

        Returns:
            ValidationResult: Result containing validity status, processed text,
                           and optional feedback.

        Example:
            >>> processor = MyProcessor()
            >>> result = processor("hello world")
            >>> print(result.valid)
            True
        """
        return self.process_output(text, **kwargs)
