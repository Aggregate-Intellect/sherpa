import uuid

import chromadb 
from chromadb.utils import embedding_functions 
from langchain_core.documents import Document 
from langchain_text_splitters import CharacterTextSplitter 

import sherpa_ai.config as cfg
from sherpa_ai.connectors.base import BaseVectorDB


class ChromaVectorStore(BaseVectorDB):
    """
    A class used to represent a Chroma Vector Store.

    This class provides methods to create a Chroma Vector Store from texts or from an existing store,
    split file text, and perform a similarity search.

    ...

    Attributes
    ----------
    db : chromadb.PersistentClient
        a persistent client to interact with the ChromaDB

    Methods
    -------
    chroma_from_texts(texts, embedding, meta_datas)
        Class method to create a Chroma Vector Store from given texts.
    chroma_from_existing(embedding)
        Class method to create a Chroma Vector Store from an existing store.
    file_text_splitter(data, meta_data)
        Class method to split file text into chunks.
    similarity_search(query, session_id)
        Method to perform a similarity search in the Chroma Vector Store.
    """

    def __init__(self, db, path="./db") -> None:
        self.db = db
        self.path = path

    @classmethod
    def chroma_from_texts(
        cls,
        texts,
        embedding=None,
        meta_datas=None,
        path="./db",
    ):
        # Use OpenAIEmbeddingFunction as default embedding function, this cannot be in the
        # method signature for mocking purposes
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

        return cls(db, path)

    @classmethod
    def chroma_from_existing(
        cls,
        embedding=None,
        path="./db",
    ):
        # Use OpenAIEmbeddingFunction as default embedding function, this cannot be in the
        # method signature for mocking purposes
        if embedding is None:
            embedding = embedding_functions.OpenAIEmbeddingFunction(
                model_name="text-embedding-ada-002"
            )

        client = chromadb.PersistentClient(path=path)
        db = client.get_or_create_collection(
            name=cfg.INDEX_NAME_FILE_STORAGE, embedding_function=embedding
        )

        return cls(db)

    def similarity_search(
        self, query: str = "", session_id: str = None, number_of_results=2, k: int = 1
    ):
        filter = {} if session_id is None else {"session_id": session_id}
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
