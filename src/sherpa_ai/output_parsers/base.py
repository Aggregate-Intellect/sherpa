from abc import ABC, abstractmethod
from typing import Tuple


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
    def parse_output(self, text: str) -> str:
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
        None

    Methods:
        process_output(text: str) -> Tuple[bool, str]:
            This method should be implemented by subclasses to process the input text.

        __call__(text: str) -> Tuple[bool, str]:
            This method is a convenient shorthand for calling process_output.
            It is implemented to call process_output and return the result.

    """

    @abstractmethod
    def process_output(self, text: str) -> Tuple[bool, str]:
        """
        Abstract method to be implemented by subclasses for processing output text.

        Parameters:
            text (str): The input text to be processed.

        Returns:
            Tuple[bool, str]: A tuple containing a boolean indicating success or failure,
                             and the processed output text.
        """
        pass

    def __call__(self, text: str) -> Tuple[bool, str]:
        return self.process_output(text)
