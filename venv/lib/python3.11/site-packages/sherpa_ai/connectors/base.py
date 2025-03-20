from abc import ABC, abstractmethod
from typing import List

from langchain_core.documents import Document 


class BaseVectorDB(ABC):
    def __init__(self, db):
        self.db = db

    @abstractmethod
    def similarity_search(
        self, query: str, number_of_results: int, k: int, session_id: str = None
    ) -> List[Document]:
        pass
