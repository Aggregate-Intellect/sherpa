from abc import ABC, abstractmethod
from typing import Any, List, Optional

from langchain_core.documents import Document
from pydantic import BaseModel, ConfigDict, Field


class BaseVectorDB(ABC, BaseModel):
    """Abstract base class for vector database connectors with Pydantic validation.

    This class defines the interface that all vector database connectors must implement,
    providing methods for similarity search operations with automatic data validation.

    Attributes:
        db: The underlying database connection or client.

    Example:
        >>> from sherpa_ai.connectors.base import BaseVectorDB
        >>> from sherpa_ai.connectors.chroma_vector_store import ChromaVectorStore
        >>> # ChromaVectorStore implements BaseVectorDB
        >>> vector_db = ChromaVectorStore(db=some_db)
        >>> results = vector_db.similarity_search("query", number_of_results=5)
    """
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    db: Any = Field(..., description="The underlying database connection or client")

    @abstractmethod
    def similarity_search(
        self, 
        query: str, 
        number_of_results: int, 
        k: int, 
        session_id: Optional[str] = None
    ) -> List[Document]:
        """Perform a similarity search in the vector database.

        This method searches for documents that are semantically similar to the query.
        All parameters are automatically validated by Pydantic.

        Args:
            query (str): The search query.
            number_of_results (int): The number of results to return.
            k (int): The number of nearest neighbors to consider.
            session_id (Optional[str]): Session ID to filter results. Defaults to None.

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
