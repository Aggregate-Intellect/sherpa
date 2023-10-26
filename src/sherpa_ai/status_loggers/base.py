from abc import ABC, abstractmethod


class BaseStatusLogger(ABC):
    @abstractmethod
    def log(self, message: str):
        pass
