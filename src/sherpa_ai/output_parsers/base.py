from abc import ABC, abstractmethod
from typing import Tuple


class BaseOutputParser(ABC):
    """
    An abstract base class for output parsers.

    All concrete output parser classes should inherit from this base class
    and implement the abstract method 'parse_output'.

    Attributes:
    - None

    @abstractmethod
    def parse_output(self, text: str) -> str:
        pass

    Methods:
    - parse_output(text: str) -> str:
        This abstract method must be implemented by subclasses to define
        the logic for parsing the given text and returning the parsed output.

    Example Usage:
    ```python
    class MyOutputParser(BaseOutputParser):
        def parse_output(self, text: str) -> str:
            # Implement custom logic to parse the output from 'text'
            # and return the parsed result.
            pass
    ```
    """

    @abstractmethod
    def process_output(self, text: str) -> Tuple[bool, str]:
        """
        Parse the output from the given text.

        This method should be implemented by concrete subclasses to define
        the logic for parsing the output from the provided 'text' and returning
        the parsed result.

        Parameters:
        - text (str): The raw text to be parsed.

        Returns:
        - str: The parsed output.
        """
        pass

    def __call__(self, text: str) -> Tuple[bool, str]:
        return self.process_output(text)
