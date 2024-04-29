import json
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ActionResource:
    """
    Resource used for an action.

    Attributes:
        source (str): Source of the resource, such as document id or url.
        content (str): Content of the resource.
    """

    source: str
    content: str


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

    @property
    def resources(self) -> list:
        return []

    def __str__(self):
        tool_desc = {
            "name": self.name,
            "args": self.args,
        }

        return json.dumps(tool_desc, indent=4)
