from langchain.document_loaders import PDFMinerLoader
from langchain.embeddings.base import Embeddings
from langchain.text_splitter import SentenceTransformersTokenTextSplitter
from langchain.vectorstores.chroma import Chroma
from loguru import logger
from pydantic import ConfigDict

from sherpa_ai.actions.base import BaseAction


class DocumentSearch(BaseAction):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    # file name of the pdf
    filename: str
    # the embedding function to use
    embedding_function: Embeddings
    # number of results to return in search
    k: int
    # the variables start with _ will not included in the __init__
    _chroma: Chroma
    # Override name and args properties from BaseAction
    # The name of the action, used to describe the action to the agent.
    name: str = "DocumentSearch"
    # The arguments that the action takes, used to describe the action to the agent.
    args: dict = {"query": "string"}
    # Description of action. Used semantically to determine when the action should be chosen by the agent
    usage: str = "Search the document store based on a query"

    def __init__(self, **kwargs):
        # initialize attributes using Pydantic BaseModel
        super().__init__(**kwargs)

        # load the pdf and create the vector store
        self._chroma = Chroma(embedding_function=self.embedding_function)
        documents = PDFMinerLoader(self.filename).load()
        documents = SentenceTransformersTokenTextSplitter(
            chunk_overlap=0
        ).split_documents(documents)

        logger.info(f"Adding {len(documents)} documents to the vector store")
        self._chroma.add_documents(documents)
        logger.info("Finished adding documents to the vector store")

    def execute(self, query):
        """
        Execute the action by searching the document store for the query

        Args:
            query (str): The query to search for

        Returns:
            str: The search results combined into a single string
        """

        results = self._chroma.search(query, search_type="mmr", k=self.k)
        return "\n\n".join([result.page_content for result in results])