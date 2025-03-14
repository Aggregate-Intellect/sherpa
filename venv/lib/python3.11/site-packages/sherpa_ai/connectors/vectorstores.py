import os
import uuid
from typing import Any, Iterable, List, Optional, Tuple, Type

import chromadb 
import pinecone 
from langchain_community.vectorstores import Chroma 
from langchain_core.documents import Document 
from langchain_core.embeddings import Embeddings 
from langchain_core.vectorstores import ( 
    VectorStore,
    VectorStoreRetriever,
)
from langchain_openai import OpenAIEmbeddings 

from langchain_text_splitters import CharacterTextSplitter 
from loguru import logger 

import sherpa_ai.config as cfg
from sherpa_ai.utils import load_files


class ConversationStore(VectorStore):
    def __init__(self, namespace, db, embeddings, text_key):
        self.db = db
        self.namespace = namespace
        self.embeddings_func = embeddings
        self.text_key = text_key

    @classmethod
    def from_index(cls, namespace, openai_api_key, index_name, text_key="text"):
        pinecone.init(api_key=cfg.PINECONE_API_KEY,
                      environment=cfg.PINECONE_ENV)
        logger.info(f"Loading index {index_name} from Pinecone")
        index = pinecone.Index(index_name)
        embedding = OpenAIEmbeddings(openai_api_key=openai_api_key)
        return cls(namespace, index, embedding, text_key)

    def add_text(self, text: str, metadata={}) -> str:
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
        for text, metadata in zip(texts, metadatas):
            self.add_text(text, metadata)

    def similarity_search(
        self,
        text: str,
        top_k: int = 5,
        filter: Optional[dict] = None,
        threshold: float = 0.7,
    ) -> list[Document]:
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
        pinecone.init(api_key=cfg.PINECONE_API_KEY,
                      environment=cfg.PINECONE_ENV)
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
        vectorstore = cls.from_index(namespace, openai_api_key, index_name)
        retriever = VectorStoreRetriever(
            vectorstore=vectorstore,
            search_type=search_type,
            search_kwargs=search_kwargs,
        )
        return retriever

    @classmethod
    def from_texts(cls, texts: List[str], embedding: Embeddings, metadatas: list[dict]):
        raise NotImplementedError(
            "ConversationStore does not support from_texts")


class LocalChromaStore(Chroma):
    @classmethod
    def from_folder(cls, file_path, openai_api_key, index_name="chroma"):
        """
        Create a Chroma DB from a folder of files (Currently only supports pdfs and
        markdown files)
        file_path: path to the folder
        openai_api_key: openai api key
        index_name: name of the index
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
    client = chromadb.HttpClient(host=cfg.CHROMA_HOST, port=cfg.CHROMA_PORT)
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    chroma = Chroma(
        client=client, collection_name=cfg.CHROMA_INDEX, embedding_function=embeddings
    )
    return chroma


def get_vectordb():
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
        if os.path.exists("files"):
            return LocalChromaStore.from_folder(
                "files", cfg.OPENAI_API_KEY
            ).as_retriever()
        else:
            logger.warning(
                "No files folder found, initialize an empty vectorstore instead"
            )
            embedding_func = OpenAIEmbeddings(
                openai_api_key=cfg.OPENAI_API_KEY)
            return LocalChromaStore(
                "memory", embedding_function=embedding_func
            ).as_retriever()
