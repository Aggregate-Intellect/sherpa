"""
Different methods for reranking the results of a search query.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable

import numpy as np
from numpy.typing import ArrayLike
from pydantic import BaseModel


def cosine_similarity(v1: ArrayLike, v2: ArrayLike) -> float:
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))


class BaseReranking(ABC, BaseModel):
    @abstractmethod
    def rerank(self, documents: list[str], **kwargs) -> str:
        pass


class RerankingByQuery(BaseReranking):
    embeddings: Any  # takes an Embedding Object from LangChain, use Any since it is not compatible with Pydantic 2 yet
    distance_metric: Callable[[ArrayLike, ArrayLike], float] = cosine_similarity

    def rerank(self, documents: list[str], query: str) -> str:
        query_embedding = self.embeddings.embed_query(query)
        document_embeddings = self.embeddings.embed_documents(documents)

        # Calculate the similarity between the query and each document
        similarities = [
            self.distance_metric(query_embedding, doc_embedding)
            for doc_embedding in document_embeddings
        ]

        # Sort the documents by similarity
        sorted_documents = [
            doc for _, doc in sorted(zip(similarities, documents), reverse=True)
        ]

        return sorted_documents
