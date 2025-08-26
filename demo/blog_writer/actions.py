from langchain_community.document_loaders import PDFMinerLoader 
from langchain_chroma import Chroma 
from langchain_text_splitters import SentenceTransformersTokenTextSplitter 
from loguru import logger 

from sherpa_ai.actions.base import BaseAction


class DocumentSearch(BaseAction):
    def __init__(self, filename, embedding_function, k=4):
        # file name of the pdf
        self.filename = filename
        # the embedding function to use
        self.embedding_function = embedding_function
        # number of results to return in search
        self.k = k

        # load the pdf and create the vector store
        self.chroma = Chroma(embedding_function=embedding_function)
        documents = PDFMinerLoader(self.filename).load()
        documents = SentenceTransformersTokenTextSplitter(
            chunk_overlap=0).split_documents(documents)

        logger.info(f"Adding {len(documents)} documents to the vector store")
        self.chroma.add_documents(documents)
        logger.info("Finished adding documents to the vector store")

    def execute(self, query):
        """
        Execute the action by searching the document store for the query

        Args:
            query (str): The query to search for

        Returns:
            str: The search results combined into a single string
        """

        results = self.chroma.search(query, search_type="mmr", k=self.k)
        return "\n\n".join([result.page_content for result in results])

    @property
    def name(self) -> str:
        """
        The name of the action, used to describe the action to the agent.
        """
        return "DocumentSearch"

    @property
    def args(self) -> dict:
        """
        The arguments that the action takes, used to describe the action to the agent.
        """
        return {
            "query": "string"
        }
