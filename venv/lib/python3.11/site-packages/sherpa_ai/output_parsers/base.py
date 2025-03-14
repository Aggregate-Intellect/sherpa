from abc import ABC, abstractmethod
from typing import Tuple

from sherpa_ai.output_parsers.validation_result import ValidationResult


class BaseOutputParser(ABC):
    """
    Abstract base class for output parsers.

    Defines the interface for parsing output text.

    Attributes:
        None

    Methods:
        parse_output(text: str) -> str:
            This method should be implemented by subclasses to parse the input text.

    """

    @abstractmethod
    def parse_output(text: str, **kwargs) -> str:
        """
        Abstract method to be implemented by subclasses for parsing output text.

        Parameters:
            text (str): The input text to be parsed.

        Returns:
            str: The parsed output text.
        """
        pass


class BaseOutputProcessor(ABC):
    """
    Abstract base class for output processors.

    Defines the interface for processing output text.

    Attributes:
        count (int): Abstract global variable representing the count of failed validations.

    Methods:
        process_output(text: str) -> Tuple[bool, str]:
            This method should be implemented by subclasses to process the input text.

        __call__(text: str) -> Tuple[bool, str]:
            This method is a convenient shorthand for calling process_output.
            It is implemented to call process_output and return the result.

    """

    count: int = 0

    def reset_state(self):
        self.count = 0

    @abstractmethod
    def process_output(self, text: str, **kwargs) -> ValidationResult:
        """
        Abstract method to be implemented by subclasses for processing output text.

        Parameters:
            text (str): The input text to be processed.

        Returns:
            ValidationResult: The result of the processing, including the validity status,
            the processed text, and optional feedback.
        """
        pass

    def __call__(self, text: str, **kwargs) -> ValidationResult:
        return self.process_output(text, **kwargs)
