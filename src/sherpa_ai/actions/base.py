from abc import ABC, abstractmethod


class BaseAction(ABC):
    @abstractmethod
    def execute(self, **kwargs):
        pass
