from abc import ABC, abstractmethod


class BaseOutputParser(ABC):
    @abstractmethod
    def parse_output(self, text: str) -> str:
        pass
