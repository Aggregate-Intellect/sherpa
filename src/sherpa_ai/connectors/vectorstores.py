import os
import uuid
from typing import Any, Iterable, List, Optional, Tuple, Type

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore, VectorStoreRetriever
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from loguru import logger

import sherpa_ai.config as cfg
from sherpa_ai.utils import load_files


class ConversationStore(VectorStore):
    """A vector store for storing and retrieving conversation data.

    This class provides methods to store conversation data in a vector database
    and retrieve similar conversations based on queries.

    Attributes:
        db: The underlying database connection.
        namespace (str): The namespace for the vector store.
        embeddings_func: The embedding function to use.
        text_key (str): The key used to store the text in metadata.

    Example:
        >>> from sherpa_ai.connectors.vectorstores import ConversationStore
        >>> store = ConversationStore.from_index("my_namespace", "api_key", "my_index")
        >>> store.add_text("This is a conversation", {"user": "user1"})
        >>> results = store.similarity_search("conversation", top_k=5)
    """
    def __init__(self, namespace, db, embeddings, text_key):
        """Initialize a ConversationStore instance.

        Args:
            namespace (str): The namespace for the vector store.
            db: The database connection.
            embeddings: The embedding function to use.
            text_key (str): The key used to store the text in metadata.

        Example:
            >>> from sherpa_ai.connectors.vectorstores import ConversationStore
            >>> store = ConversationStore("my_namespace", db, embeddings, "text")
        """
        self.db = db
        self.namespace = namespace
        self.embeddings_func = embeddings
        self.text_key = text_key

    @classmethod
    def from_index(cls, namespace, openai_api_key, index_name, text_key="text"):
        """Create a ConversationStore from a Pinecone index.

        This method initializes a Pinecone client and creates a ConversationStore
        instance connected to the specified index.

        Args:
            namespace (str): The namespace for the vector store.
            openai_api_key (str): The OpenAI API key.
            index_name (str): The name of the Pinecone index.
            text_key (str, optional): The key used to store the text in metadata. Defaults to "text".

        Returns:
            ConversationStore: A new ConversationStore instance.

        Raises:
            ImportError: If the pinecone-client package is not installed.

        Example:
            >>> from sherpa_ai.connectors.vectorstores import ConversationStore
            >>> store = ConversationStore.from_index("my_namespace", "api_key", "my_index")
        """
        try:
            import pinecone
        except ImportError:
            raise ImportError(
                "Could not import pinecone-client python package. "
                "This is needed in order to to use ConversationStore. "
                "Please install it with `pip install pinecone-client`"
            )

        pinecone.init(api_key=cfg.PINECONE_API_KEY, environment=cfg.PINECONE_ENV)
        logger.info(f"Loading index {index_name} from Pinecone")
        index = pinecone.Index(index_name)
        embedding = OpenAIEmbeddings(openai_api_key=openai_api_key)
        return cls(namespace, index, embedding, text_key)

    def add_text(self, text: str, metadata={}) -> str:
        """Add a single text to the vector store.

        This method embeds the text, adds it to the database with the provided metadata,
        and returns the ID of the added text.

        Args:
            text (str): The text to add.
            metadata (dict, optional): Metadata to associate with the text. Defaults to {}.

        Returns:
            str: The ID of the added text.

        Example:
            >>> from sherpa_ai.connectors.vectorstores import ConversationStore
            >>> store = ConversationStore.from_index("my_namespace", "api_key", "my_index")
            >>> id = store.add_text("This is a conversation", {"user": "user1"})
            >>> print(id)
            '123e4567-e89b-12d3-a456-426614174000'
        """
        metadata[self.text_key] = text
        id = str(uuid.uuid4())
        embedding = self.embeddings.embed_query(text)
        doc = {"id": id, "values": embedding, "metadata": metadata}
        self.db.upsert(vectors=[doc], namespace=self.namespace)

        return id

    @property
    def embeddings(self) -> Optional[Embeddings]:
        """Access the query embedding object if available."""
        return self.embeddings_func

    def add_texts(self, texts: Iterable[str], metadatas: List[dict]) -> List[str]:
        """Add multiple texts to the vector store.

        This method adds each text with its corresponding metadata to the vector store.

        Args:
            texts (Iterable[str]): The texts to add.
            metadatas (List[dict]): The metadata for each text.

        Example:
            >>> from sherpa_ai.connectors.vectorstores import ConversationStore
            >>> store = ConversationStore.from_index("my_namespace", "api_key", "my_index")
            >>> texts = ["Text 1", "Text 2"]
            >>> metadatas = [{"user": "user1"}, {"user": "user2"}]
            >>> store.add_texts(texts, metadatas)
        """
        for text, metadata in zip(texts, metadatas):
            self.add_text(text, metadata)

    def similarity_search(
        self,
        text: str,
        top_k: int = 5,
        filter: Optional[dict] = None,
        threshold: float = 0.7,
    ) -> list[Document]:
        """Perform a similarity search in the vector store.

        This method searches for texts that are semantically similar to the query.

        Args:
            text (str): The search query.
            top_k (int, optional): The number of results to return. Defaults to 5.
            filter (Optional[dict], optional): Filter criteria for the search. Defaults to None.
            threshold (float, optional): The similarity threshold. Defaults to 0.7.

        Returns:
            list[Document]: A list of documents that match the query.

        Example:
            >>> from sherpa_ai.connectors.vectorstores import ConversationStore
            >>> store = ConversationStore.from_index("my_namespace", "api_key", "my_index")
            >>> results = store.similarity_search("What is machine learning?", top_k=5)
            >>> for doc in results:
            ...     print(doc.page_content[:100])
        """
        query_embedding = self.embeddings.embed_query(text)
        results = self.db.query(
            [query_embedding],
            top_k=top_k,
            include_metadata=True,
            namespace=self.namespace,
            filter=filter,
        )

        docs = []
        for res in results["matches"]:
            metadata = res["metadata"]
            text = metadata.pop(self.text_key)
            if res["score"] > threshold:
                docs.append(Document(page_content=text, metadata=metadata))
        return docs

    def _similarity_search_with_relevance_scores(
        self,
        query: str,
        k: int = 4,
        **kwargs: Any,
    ) -> List[Tuple[Document, float]]:
        """Perform a similarity search and return documents with relevance scores.

        This method searches for texts that are semantically similar to the query
        and returns them along with their relevance scores.

        Args:
            query (str): The search query.
            k (int, optional): The number of results to return. Defaults to 4.
            **kwargs: Additional keyword arguments.

        Returns:
            List[Tuple[Document, float]]: A list of tuples containing documents and their relevance scores.

        Example:
            >>> from sherpa_ai.connectors.vectorstores import ConversationStore
            >>> store = ConversationStore.from_index("my_namespace", "api_key", "my_index")
            >>> results = store._similarity_search_with_relevance_scores("What is machine learning?")
            >>> for doc, score in results:
            ...     print(f"Score: {score}, Content: {doc.page_content[:100]}")
        """
        logger.debug("query", query)
        query_embedding = self.embeddings.embed_query(query)
        results = self.db.query(
            [query_embedding],
            top_k=k,
            include_metadata=True,
            namespace=self.namespace,
            filter=kwargs.get("filter", None),
        )

        docs_with_score = []
        for res in results["matches"]:
            metadata = res["metadata"]
            text = metadata.pop(self.text_key)
            docs_with_score.append(
                (Document(page_content=text, metadata=metadata), res["score"])
            )
        logger.debug(docs_with_score)
        return docs_with_score

    @classmethod
    def delete(cls, namespace, index_name):
        """Delete all vectors in a namespace.

        This method deletes all vectors in the specified namespace of the Pinecone index.

        Args:
            namespace (str): The namespace to delete.
            index_name (str): The name of the Pinecone index.

        Returns:
            The result of the delete operation.

        Raises:
            ImportError: If the pinecone-client package is not installed.

        Example:
            >>> from sherpa_ai.connectors.vectorstores import ConversationStore
            >>> ConversationStore.delete("my_namespace", "my_index")
        """
        try:
            import pinecone
        except ImportError:
            raise ImportError(
                "Could not import pinecone-client python package. "
                "This is needed in order to to use ConversationStore. "
                "Please install it with `pip install pinecone-client`"
            )


        pinecone.init(api_key=cfg.PINECONE_API_KEY, environment=cfg.PINECONE_ENV)
        index = pinecone.Index(index_name)
        return index.delete(delete_all=True, namespace=namespace)

    @classmethod
    def get_vector_retrieval(
        cls,
        namespace: str,
        openai_api_key: str,
        index_name: str,
        search_type="similarity",
        search_kwargs={},
    ) -> VectorStoreRetriever:
        """Create a vector store retriever.

        This method creates a ConversationStore and returns a VectorStoreRetriever
        for it.

        Args:
            namespace (str): The namespace for the vector store.
            openai_api_key (str): The OpenAI API key.
            index_name (str): The name of the Pinecone index.
            search_type (str, optional): The type of search to perform. Defaults to "similarity".
            search_kwargs (dict, optional): Additional keyword arguments for the search. Defaults to {}.

        Returns:
            VectorStoreRetriever: A retriever for the vector store.

        Example:
            >>> from sherpa_ai.connectors.vectorstores import ConversationStore
            >>> retriever = ConversationStore.get_vector_retrieval("my_namespace", "api_key", "my_index")
            >>> results = retriever.get_relevant_documents("What is machine learning?")
        """
        vectorstore = cls.from_index(namespace, openai_api_key, index_name)
        retriever = VectorStoreRetriever(
            vectorstore=vectorstore,
            search_type=search_type,
            search_kwargs=search_kwargs,
        )
        return retriever

    @classmethod
    def from_texts(cls, texts: List[str], embedding: Embeddings, metadatas: list[dict]):
        """Create a ConversationStore from a list of texts.

        This method is not implemented for ConversationStore.

        Args:
            texts (List[str]): The texts to add.
            embedding (Embeddings): The embedding function to use.
            metadatas (list[dict]): The metadata for each text.

        Raises:
            NotImplementedError: This method is not implemented for ConversationStore.
        """
        raise NotImplementedError("ConversationStore does not support from_texts")


class LocalChromaStore:
    """A local Chroma-based vector store.

    This class extends the Chroma vector store to provide additional functionality
    for working with local files.

    Example:
        >>> from sherpa_ai.connectors.vectorstores import LocalChromaStore
        >>> store = LocalChromaStore.from_folder("path/to/files", "api_key")
        >>> results = store.similarity_search("query", k=5)
    """
    
    def __init__(self, *args, **kwargs):
        try:
            from langchain_chroma import Chroma
        except ImportError:
            raise ImportError(
                "Could not import langchain_chroma python package. "
                "This is needed in order to use LocalChromaStore. "
                "Please install it with `pip install langchain-chroma`"
            )
        self._chroma = Chroma(*args, **kwargs)
    
    def __getattr__(self, name):
        """Delegate attribute access to the underlying Chroma instance."""
        return getattr(self._chroma, name)
    @classmethod
    def from_folder(cls, file_path, openai_api_key, index_name="chroma"):
        """Create a Chroma DB from a folder of files.

        This method creates a ChromaDB from a folder of files, currently supporting
        PDFs and markdown files.

        Args:
            file_path (str): Path to the folder containing files.
            openai_api_key (str): The OpenAI API key.
            index_name (str, optional): Name of the index. Defaults to "chroma".

        Returns:
            LocalChromaStore: A new LocalChromaStore instance.

        Example:
            >>> from sherpa_ai.connectors.vectorstores import LocalChromaStore
            >>> store = LocalChromaStore.from_folder("path/to/files", "api_key")
            >>> results = store.similarity_search("query", k=5)
        """
        files = os.listdir(file_path)
        files = [file_path + "/" + file for file in files]
        documents = load_files(files)

        embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        chroma = cls(index_name, embeddings)
        test_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        documents = test_splitter.split_documents(documents)
        logger.info("adding documents")
        chroma.add_documents(documents)
        return chroma


def configure_chroma(host: str, port: int, index_name: str, openai_api_key: str):
    """Configure a ChromaDB instance.

    This function creates a ChromaDB instance connected to a remote server.

    Args:
        host (str): The host of the ChromaDB server.
        port (int): The port of the ChromaDB server.
        index_name (str): The name of the index.
        openai_api_key (str): The OpenAI API key.

    Returns:
        Chroma: A configured ChromaDB instance.

    Raises:
        ImportError: If the chromadb package is not installed.

    Example:
        >>> from sherpa_ai.connectors.vectorstores import configure_chroma
        >>> chroma = configure_chroma("localhost", 8000, "my_index", "api_key")
        >>> results = chroma.similarity_search("query", k=5)
    """
    try:
        import chromadb
    except ImportError:
        raise ImportError(
            "Could not import chromadb python package. "
            "This is needed in order to to use Chroma. "
            "Please install it with `pip install chromadb"
        )
    
    try:
        from langchain_chroma import Chroma
    except ImportError:
        raise ImportError(
            "Could not import langchain_chroma python package. "
            "This is needed in order to use Chroma. "
            "Please install it with `pip install langchain-chroma`"
        )
    client = chromadb.HttpClient(host=cfg.CHROMA_HOST, port=cfg.CHROMA_PORT)
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    chroma = Chroma(
        client=client, collection_name=cfg.CHROMA_INDEX, embedding_function=embeddings
    )
    return chroma


def _is_chroma_available():
    """Check if langchain_chroma is available."""
    try:
        import langchain_chroma
        return True
    except ImportError:
        return False


def get_vectordb():
    """Get a vector database retriever based on configuration.

    This function returns a vector database retriever based on the configuration
    in the config module. It supports Pinecone, Chroma, and local ChromaDB.

    Returns:
        VectorStoreRetriever: A retriever for the vector store.

    Example:
        >>> from sherpa_ai.connectors.vectorstores import get_vectordb
        >>> retriever = get_vectordb()
        >>> results = retriever.get_relevant_documents("What is machine learning?")
    """
    if cfg.VECTORDB == "pinecone":
        return ConversationStore.get_vector_retrieval(
            cfg.PINECONE_NAMESPACE,
            cfg.OPENAI_API_KEY,
            index_name=cfg.PINECONE_INDEX,
            search_type="similarity_score_threshold",
            search_kwargs={"score_threshold": 0.0},
        )
    elif cfg.VECTORDB == "chroma":
        return configure_chroma(
            cfg.CHROMA_HOST, cfg.CHROMA_PORT, cfg.CHROMA_INDEX, cfg.OPENAI_API_KEY
        ).as_retriever()
    else:
        # Check if langchain_chroma is available before trying to use it
        if not _is_chroma_available():
            raise ImportError(
                "Could not import langchain_chroma python package. "
                "This is needed in order to use the default vector store. "
                "Please install it with `pip install langchain-chroma` or "
                "configure a different vector database (pinecone/chroma) in your environment."
            )
        
        if os.path.exists("files"):
            return LocalChromaStore.from_folder(
                "files", cfg.OPENAI_API_KEY
            ).as_retriever()
        else:
            logger.warning(
                "No files folder found, initialize an empty vectorstore instead"
            )
            embedding_func = OpenAIEmbeddings(openai_api_key=cfg.OPENAI_API_KEY)
            return LocalChromaStore(
                "memory", embedding_function=embedding_func
            ).as_retriever()
