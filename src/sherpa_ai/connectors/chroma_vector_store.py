import uuid

import chromadb
from chromadb.utils import embedding_functions
from langchain.docstore.document import Document
from langchain.text_splitter import CharacterTextSplitter

import sherpa_ai.config as cfg


class ChromaVectorStore:
    def __init__(self, db) -> None:
        self.db = db

    @classmethod
    def chroma_from_texts(cls, texts, embedding=None, meta_datas=None):
        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            model_name="text-embedding-ada-002"
        )
        embeded_data = openai_ef(texts)
        meta_datas = [] if meta_datas is None else meta_datas
        client = chromadb.PersistentClient(path="./db")
        db = client.get_or_create_collection(
            name=cfg.INDEX_NAME_FILE_STORAGE, embedding_function=openai_ef
        )
        db.add(
            embeddings=embeded_data,
            documents=texts,
            metadatas=meta_datas,
            ids=[str(uuid.uuid1()) for text in texts],
        )

        return cls(db)

    @classmethod
    def chroma_from_existing(cls):
        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            model_name="text-embedding-ada-002"
        )

        client = chromadb.PersistentClient(path="./db")
        db = client.get_or_create_collection(
            name=cfg.INDEX_NAME_FILE_STORAGE, embedding_function=openai_ef
        )

        return cls(db)

    @classmethod
    def file_text_splitter(cls, data, meta_data):
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_text(data)
        metadatas = []
        temp_texts = []
        for doc in texts:
            metadatas.append(meta_data)
            temp_texts.append(f"""'file_content': '{doc}' ,{meta_data}""")
        texts = temp_texts

        return {"texts": texts, "meta_datas": metadatas}

    def similarity_search(self, query: str = "", session_id: str = None):
        filter = {} if session_id is None else {"session_id": session_id}
        results = self.db.query(
            query_texts=[query],
            n_results=2,
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
