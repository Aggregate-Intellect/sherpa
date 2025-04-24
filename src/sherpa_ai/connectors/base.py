from abc import ABC, abstractmethod
from typing import List

from langchain_core.documents import Document 


class BaseVectorDB(ABC):
    """Abstract base class for vector database connectors.

    This class defines the interface that all vector database connectors must implement,
    providing methods for similarity search operations.

    Attributes:
        db: The underlying database connection or client.

    Example:
        >>> from sherpa_ai.connectors.base import BaseVectorDB
        >>> from sherpa_ai.connectors.chroma_vector_store import ChromaVectorStore
        >>> # ChromaVectorStore implements BaseVectorDB
        >>> vector_db = ChromaVectorStore(db=some_db)
        >>> results = vector_db.similarity_search("query", number_of_results=5)
    """
    def __init__(self, db):
        """Initialize the vector database connector.

        Args:
            db: The database connection or client to use.

        Example:
            >>> from sherpa_ai.connectors.base import BaseVectorDB
            >>> from sherpa_ai.connectors.chroma_vector_store import ChromaVectorStore
            >>> vector_db = ChromaVectorStore(db=some_db)
        """
        self.db = db

    @abstractmethod
    def similarity_search(
        self, query: str, number_of_results: int, k: int, session_id: str = None
    ) -> List[Document]:
        """Perform a similarity search in the vector database.

        This method searches for documents that are semantically similar to the query.

        Args:
            query (str): The search query.
            number_of_results (int): The number of results to return.
            k (int): The number of nearest neighbors to consider.
            session_id (str, optional): Session ID to filter results. Defaults to None.

        Returns:
            List[Document]: A list of documents that match the query.

        Example:
            >>> from sherpa_ai.connectors.base import BaseVectorDB
            >>> from sherpa_ai.connectors.chroma_vector_store import ChromaVectorStore
            >>> vector_db = ChromaVectorStore(db=some_db)
            >>> results = vector_db.similarity_search("What is machine learning?", number_of_results=5)
            >>> for doc in results:
            ...     print(doc.page_content[:100])
        """
        pass
