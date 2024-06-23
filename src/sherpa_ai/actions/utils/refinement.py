"""
Different methods for reranking the results of a search query.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable

import numpy as np
from numpy.typing import ArrayLike
from pydantic import BaseModel


SEARCH_SUMMARY_DESCRIPTION = """ Question：{question} 
Relevant Answer:
{answer}


Review relevant answer and provide the most relevant information in at most {k} sentences."""


class BaseRefinement(ABC, BaseModel):
    @abstractmethod
    def refinement(self, documents: list[str], **kwargs) -> str:
        pass


class RefinementByQuery(BaseRefinement):
    llm: Any  # The BaseLanguageModel from LangChain is not compatible with Pydantic 2 yet
    description: str = SEARCH_SUMMARY_DESCRIPTION
    k: int = 3

    def refinement(self, documents: list[str], query: str) -> str:
        refined_result = [
            self.llm.predict(
                self.description.format(question=query, answer=doc, k=self.k)
            )
            for doc in documents
        ]
        return refined_result
