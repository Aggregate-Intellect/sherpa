import os

from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from loguru import logger

import sherpa_ai.config as cfg
from sherpa_ai.utils import load_files


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
    in the config module. It supports Chroma and local ChromaDB.

    Returns:
        VectorStoreRetriever: A retriever for the vector store.

    Example:
        >>> from sherpa_ai.connectors.vectorstores import get_vectordb
        >>> retriever = get_vectordb()
        >>> results = retriever.get_relevant_documents("What is machine learning?")
    """
    if cfg.VECTORDB == "chroma":
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
                "configure a different vector database (chroma) in your environment."
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
