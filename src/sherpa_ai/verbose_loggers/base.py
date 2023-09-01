from abc import ABC, abstractmethod


class BaseVerboseLogger(ABC):
    @abstractmethod
    def log(self, message: str):
        pass
