import json
from abc import ABC, abstractmethod


class BaseAction(ABC):
    @abstractmethod
    def execute(self, **kwargs):
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def args(self) -> dict:
        pass

    def __str__(self):
        tool_desc = {
            "name": self.name,
            "args": self.args,
        }

        return json.dumps(tool_desc, indent=4)
