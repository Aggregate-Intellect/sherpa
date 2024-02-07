from abc import ABC, abstractmethod
from typing import Tuple


class BaseOutputParser(ABC):
    @abstractmethod
    def parse_output(self, text: str) -> str:
        pass


class BaseOutputProcessor(ABC):
    @abstractmethod
    def process_output(self, text: str) -> Tuple[bool, str]:
        pass

    def __call__(self, text: str) -> Tuple[bool, str]:
        return self.process_output(text)
