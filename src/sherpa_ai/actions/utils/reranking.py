"""
Different methods for reranking the results of a search query.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable

import numpy as np
from numpy.typing import ArrayLike
from pydantic import BaseModel


def cosine_similarity(v1: ArrayLike, v2: ArrayLike) -> float:
    """Calculate the cosine similarity between two vectors.

    Args:
        v1 (ArrayLike): The first vector.
        v2 (ArrayLike): The second vector.  

    Returns:
        float: The cosine similarity between the two vectors.
    
    Raises:
        SherpaActionExecutionException: If the action fails to execute.
    """
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))


class BaseReranking(ABC, BaseModel):
    """Abstract base class for reranking actions.
    
    This class provides a base implementation for reranking actions that can be
    used to rerank search results or documents based on a query.
    
    Attributes:
        embeddings (Any): The embeddings object used for reranking.
        distance_metric (Callable[[ArrayLike, ArrayLike], float]): The distance metric used for reranking.
    
    Example:
        >>> from sherpa_ai.actions.utils import RerankingByQuery
        >>> reranking = RerankingByQuery(embeddings=my_embeddings)
        >>> results = reranking.rerank(documents, query)
    """
    @abstractmethod
    def rerank(self, documents: list[str], **kwargs) -> str:
        pass


class RerankingByQuery(BaseReranking):
    """Reranking action that reranks search results based on a query.
    
    This class provides a reranking action that reranks search results based on a query.
    It uses an embeddings object to embed the query and documents, and then calculates
    the cosine similarity between the query and each document.

    Attributes:
        embeddings (Any): The embeddings object used for reranking.
        distance_metric (Callable[[ArrayLike, ArrayLike], float]): The distance metric used for reranking.
    
    Example:
        >>> from sherpa_ai.actions.utils import RerankingByQuery
        >>> reranking = RerankingByQuery(embeddings=my_embeddings)
        >>> results = reranking.rerank(documents, query)
    """
    embeddings: Any = None  # takes an Embedding Object from LangChain, use Any since it is not compatible with Pydantic 2 yet
    distance_metric: Callable[[ArrayLike, ArrayLike], float] = cosine_similarity

    def rerank(self, documents: list[str], query: str) -> str:
        """Rerank the documents based on the query.

        Args:
            documents (list[str]): The documents to rerank.
            query (str): The query to rerank the documents.
        
        Returns:
            list[str]: The reranked documents.

        Raises:
            SherpaActionExecutionException: If the action fails to execute.
        """
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
