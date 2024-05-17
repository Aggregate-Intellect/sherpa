import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import cached_property

from pydantic import BaseModel, Field


class ActionResource(BaseModel):
    """
    Resource used for an action.

    Attributes:
        source (str): Source of the resource, such as document id or url.
        content (str): Content of the resource.
    """

    source: str
    content: str


class BaseAction(ABC, BaseModel):
    name: str
    args: dict

    @abstractmethod
    def execute(self, **kwargs):
        pass

    def __str__(self):
        tool_desc = {
            "name": self.name,
            "args": self.args,
        }

        return json.dumps(tool_desc, indent=4)


class BaseRetrievalAction(BaseAction, ABC):
    resources: list[ActionResource] = Field(default_factory=list)

    def add_resources(self, resources: list[dict]):
        action_resources = self.resources
        action_resources.clear()

        for resource in resources:
            action_resources.append(
                ActionResource(source=resource["Source"], content=resource["Document"])
            )
