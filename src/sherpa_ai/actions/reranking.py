"""
Different methods for reranking the results of a search query.
"""

from abc import ABC, abstractmethod
from typing import Any

import numpy as np
from langchain.embeddings import OpenAIEmbeddings
from pydantic import BaseModel


class BaseReranking(ABC, BaseModel):
    @abstractmethod
    def rerank(self, documents: list[str], **kwargs) -> str:
        pass


class RerankingByQuery(BaseReranking):
    embedding_func: Any = OpenAIEmbeddings(model_name="text-embedding-3-small")

    def rerank(self, documents: list[str], query: str) -> str:
        query_embedding = self.embedding_func(query)
        document_embeddings = [self.embedding_func(doc) for doc in documents]

        # Calculate the similarity between the query and each document
        similarities = [
            cosine_similarity(query_embedding, doc_embedding)
            for doc_embedding in document_embeddings
        ]

        # Sort the documents by similarity
        sorted_documents = [
            doc for _, doc in sorted(zip(similarities, documents), reverse=True)
        ]

        return sorted_documents


def cosine_similarity(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
