import os
from typing import Any

from langchain_community.document_loaders import PDFMinerLoader
from langchain_community.vectorstores import Chroma
from langchain_core.embeddings import Embeddings
from langchain_core.prompts import PromptTemplate
from langchain_text_splitters import SentenceTransformersTokenTextSplitter
from loguru import logger
from tqdm import tqdm

from sherpa_ai.actions.base import BaseAction
from sherpa_ai.events import Event, EventType

PROMPT = """Use the following information, summarize it to answer the task.
{information}


The task is: "{question}"


Answer:
"""


class StartQuestion(BaseAction):
    """
    Waiting the user to ask a question.
    """

    name: str = "StartQuestion"
    args: dict = {}
    usage: str = "Waiting the user to ask a question"

    def execute(self) -> str:
        question = input("Ask me a question: ")
        self.belief.set_current_task(Event(EventType.task, "user", question))

        return "success"


class Summarize(BaseAction):
    name: str = "Summarize"
    args: dict = {
        "question": "string",
    }
    usage: str = "Summarize the information to answer the question"

    llm: Any
    prompt: str = PROMPT

    def execute(self, question: str) -> str:
        prompt = PromptTemplate.from_template(self.prompt)

        pipe = prompt | self.llm

        info = "\n".join(
            [document.page_content for document in self.belief.get(
                "search_results")]
        )

        result = pipe.invoke(
            {"information": info, "question": question}).content

        logger.info(result)

        return result


class MultiDocumentSearchAction(BaseAction):
    folder_path: str
    embedding_function: Embeddings
    k: int

    filenames: list[str] = []
    file_count: int = 0
    _chroma: Chroma
    name: str = "MultiDocumentSearch"
    args: dict = {"query": "string"}
    usage_template: str = (
        "Search the document store based on a query for document {count}"
    )
    usage: str = usage_template

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._chroma = Chroma(
            embedding_function=self.embedding_function,
            persist_directory=f"{self.folder_path}/chroma_db",
        )
        self.filenames = os.listdir(self.folder_path)

        if len(self._chroma) == 0:
            for filename in tqdm(self.filenames, desc="Loading documents"):
                if ".pdf" not in filename:
                    continue
                self.load_document(f"{self.folder_path}/{filename}")

    def execute(self, query: str) -> str:
        if self.file_count >= len(self.filenames):
            return "False"

        if self.file_count == 0:
            self.belief.set("search_results", [])

        filename = self.filenames[self.file_count]
        results = self._chroma.search(
            query,
            search_type="mmr",
            k=self.k,
            filter={"filename": f"{self.folder_path}/{filename}"},
        )

        self.belief.get("search_results").extend(results)
        self.file_count = self.file_count + 1
        logger.error([result.metadata for result in results])
        return "\n\n".join([result.page_content for result in results])

    def is_finished(self):
        is_finished = self.file_count >= len(self.filenames)

        if is_finished:
            self.file_count = 0

        return is_finished

    def load_document(self, filename: str):
        documents = PDFMinerLoader(filename).load()
        documents = SentenceTransformersTokenTextSplitter(
            chunk_overlap=0
        ).split_documents(documents)

        logger.info(f"Adding {len(documents)} documents to the vector store")
        for document in documents:
            document.metadata["filename"] = filename
        self._chroma.add_documents(documents)
        logger.info("Finished adding documents to the vector store")

    def __str__(self):
        self.usage = self.usage_template.format(count=self.file_count)
        return super().__str__()
