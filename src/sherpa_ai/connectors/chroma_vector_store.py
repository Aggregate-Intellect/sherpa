import uuid
from typing import Any, List, Optional

import chromadb
from chromadb.utils import embedding_functions
from langchain_core.documents import Document
from pydantic import Field

import sherpa_ai.config as cfg
from sherpa_ai.connectors.base import BaseVectorDB


class ChromaVectorStore(BaseVectorDB):
    """A Chroma-based vector store for document retrieval.

    This class provides methods to create a Chroma Vector Store from texts or from an 
    existing store, split file text, and perform similarity searches.

    Attributes:
        db: A persistent client to interact with the ChromaDB.
        path (str): The path to the database storage. Defaults to "./db".

    Example:
        >>> from sherpa_ai.connectors.chroma_vector_store import ChromaVectorStore
        >>> texts = ["This is a sample document", "Another document for testing"]
        >>> vector_store = ChromaVectorStore.chroma_from_texts(texts)
        >>> results = vector_store.similarity_search("sample", number_of_results=1)
        >>> print(results[0].page_content)
        This is a sample document
    """

    path: str = Field(default="./db", description="Path to the database storage")

    @classmethod
    def chroma_from_texts(
        cls,
        texts,
        embedding=None,
        meta_datas=None,
        path="./db",
    ):
        """Create a ChromaVectorStore from a list of texts.

        This method creates a new ChromaDB collection, embeds the texts, and adds them
        to the collection.

        Args:
            texts: List of text documents to embed and store.
            embedding: Embedding function to use. If None, uses OpenAI's text-embedding-ada-002.
            meta_datas: List of metadata dictionaries for each text. Defaults to None.
            path (str, optional): Path to the database storage. Defaults to "./db".

        Returns:
            ChromaVectorStore: A new ChromaVectorStore instance.

        Example:
            >>> from sherpa_ai.connectors.chroma_vector_store import ChromaVectorStore
            >>> texts = ["This is a sample document", "Another document for testing"]
            >>> vector_store = ChromaVectorStore.chroma_from_texts(texts)
            >>> print(vector_store.db.count())
            2
        """
        # Use OpenAIEmbeddingFunction as default embedding function, this cannot be in
        # the method signature for mocking purposes
        if embedding is None:
            embedding = embedding_functions.OpenAIEmbeddingFunction(
                model_name="text-embedding-ada-002"
            )

        embeded_data = embedding(texts)
        meta_datas = [] if meta_datas is None else meta_datas
        client = chromadb.PersistentClient(path=path)
        db = client.get_or_create_collection(
            name=cfg.INDEX_NAME_FILE_STORAGE, embedding_function=embedding
        )

        db.add(
            embeddings=embeded_data,
            documents=texts,
            metadatas=meta_datas,
            ids=[str(uuid.uuid1()) for _ in texts],
        )

        return cls(db=db, path=path)

    @classmethod
    def chroma_from_existing(
        cls,
        embedding=None,
        path="./db",
    ):
        """Create a ChromaVectorStore from an existing ChromaDB collection.

        This method connects to an existing ChromaDB collection or creates a new one
        if it doesn't exist.

        Args:
            embedding: Embedding function to use. If None, uses OpenAI's text-embedding-ada-002.
            path (str, optional): Path to the database storage. Defaults to "./db".

        Returns:
            ChromaVectorStore: A new ChromaVectorStore instance.

        Example:
            >>> from sherpa_ai.connectors.chroma_vector_store import ChromaVectorStore
            >>> vector_store = ChromaVectorStore.chroma_from_existing()
            >>> results = vector_store.similarity_search("query", number_of_results=5)
        """
        # Use OpenAIEmbeddingFunction as default embedding function, this cannot be in
        # the method signature for mocking purposes
        if embedding is None:
            embedding = embedding_functions.OpenAIEmbeddingFunction(
                model_name="text-embedding-ada-002"
            )

        client = chromadb.PersistentClient(path=path)
        db = client.get_or_create_collection(
            name=cfg.INDEX_NAME_FILE_STORAGE, embedding_function=embedding
        )

        return cls(db=db)

    def similarity_search(
        self, 
        query: str, 
        number_of_results: int, 
        k: int, 
        session_id: Optional[str] = None
    ) -> List[Document]:
        """Perform a similarity search in the ChromaDB collection.

        This method searches for documents that are semantically similar to the query.

        Args:
            query (str): The search query.
            number_of_results (int): Number of results to return.
            k (int): Number of nearest neighbors to consider.
            session_id (Optional[str]): Session ID to filter results. Defaults to None.

        Returns:
            List[Document]: A list of documents that match the query.

        Example:
            >>> from sherpa_ai.connectors.chroma_vector_store import ChromaVectorStore
            >>> vector_store = ChromaVectorStore.chroma_from_existing()
            >>> results = vector_store.similarity_search("What is machine learning?", number_of_results=5, k=1)
            >>> for doc in results:
            ...     print(doc.page_content[:100])
        """
        filter = None if session_id is None else {"session_id": session_id}
        results = self.db.query(
            query_texts=[query],
            n_results=number_of_results,
            where=filter,
            include=["documents", "metadatas"],
        )
        documents = []
        if results is not None:
            for i in range(0, len(results["documents"][0])):
                documents.append(
                    Document(
                        metadata=results["metadatas"][0][i],
                        page_content=results["documents"][0][i],
                    )
                )
        return documents
