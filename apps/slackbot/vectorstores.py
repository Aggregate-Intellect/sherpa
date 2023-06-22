from langchain.embeddings import OpenAIEmbeddings
from langchain.embeddings.base import Embeddings
from langchain.vectorstores.base import VectorStore
import pinecone
import os
import uuid
from typing import Any, Iterable, List, Optional, Type
from langchain.docstore.document import Document
import logging
from langchain.vectorstores.base import VectorStoreRetriever

PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_ENV = os.environ.get("PINECONE_ENV")


class ConversationStore(VectorStore):
    def __init__(self, namespace, db, embeddings, text_key):
        self.db = db
        self.namespace = namespace
        self.embeddings = embeddings
        self.text_key = text_key

    @classmethod
    def from_index(cls, namespace, openai_api_key, index_name, text_key="text"):
        pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
        logging.info(f"Loading index {index_name} from Pinecone")
        index = pinecone.Index(index_name)
        embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        return cls(namespace, index, embeddings, text_key)

    def add_text(self, text: str, metadata={}) -> str:
        metadata[self.text_key] = text
        id = str(uuid.uuid4())
        embedding = self.embeddings.embed_query(text)
        doc = {"id": id, "values": embedding, "metadata": metadata}
        self.db.upsert(vectors=[doc], namespace=self.namespace)

        return id

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

        # print(results)
        docs = []
        for res in results["matches"]:
            metadata = res["metadata"]
            text = metadata.pop(self.text_key)
            if res["score"] > threshold:
                docs.append(Document(page_content=text, metadata=metadata))
        return docs

    @classmethod
    def delete(cls, namespace, index_name):
        pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
        index = pinecone.Index(index_name)
        return index.delete(delete_all=True, namespace=namespace)

    @classmethod
    def get_vector_retrieval(
        cls, namespace: str, openai_api_key: str, index_name: str
    ) -> VectorStoreRetriever:
        vectorstore = cls.from_index(namespace, openai_api_key, index_name)
        retriever = VectorStoreRetriever(vectorstore=vectorstore)
        return retriever

    @classmethod
    def from_texts(cls, texts: List[str], embedding: Embeddings, metadatas: list[dict]):
        raise NotImplementedError("ConversationStore does not support from_texts")
