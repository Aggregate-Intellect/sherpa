from __future__ import annotations

import json
from abc import ABC, abstractmethod

from loguru import logger
from pydantic import BaseModel, Field

from sherpa_ai.actions.utils.refinement import BaseRefinement
from sherpa_ai.actions.utils.reranking import BaseReranking


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
    usage: str

    @abstractmethod
    def execute(self, **kwargs):
        pass

    def __call__(self, **kwargs):
        return self.execute(**kwargs)

    def __str__(self):
        tool_desc = {"name": self.name, "args": self.args, "usage": self.usage}

        return json.dumps(tool_desc, indent=4)

    def __repr__(self):
        return self.__str__()


class BaseRetrievalAction(BaseAction, ABC):
    resources: list[ActionResource] = Field(default_factory=list)
    num_documents: int = 5  # Number of documents to retrieve
    reranker: BaseReranking = None
    refiner: BaseRefinement = None
    current_task: str = ""

    perform_reranking: bool = False
    perform_refinement: bool = False

    def add_resources(self, resources: list[dict]):
        action_resources = self.resources
        action_resources.clear()

        for resource in resources:
            action_resources.append(
                ActionResource(source=resource["Source"], content=resource["Document"])
            )

    def execute(self, query: str) -> str:
        results = self.search(query)

        results = [result["Document"] for result in results]

        if self.perform_reranking:
            results = self.reranking(results)
        if self.perform_refinement:
            results = self.refine(results)
        results = "\n\n".join(results)
        logger.debug("Action Results: {}", results)

        return results

    @abstractmethod
    def search(self, query: str) -> str:
        """
        Search for relevant documents based on the query.
        """
        pass

    def reranking(self, documents: list[str]) -> list[str]:
        """
        Rerank the documents based on the query.
        """
        return self.reranker.rerank(documents, self.current_task)

    def refine(self, documents: list[str]) -> list[str]:
        """
        Refine the results based on the query.
        """
        return self.refiner.refinement(documents, self.current_task)
