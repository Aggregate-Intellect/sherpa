from typing import Any

from loguru import logger

from sherpa_ai.actions.base import BaseRetrievalAction
from sherpa_ai.connectors.vectorstores import get_vectordb
from sherpa_ai.tools import ContextTool


SEARCH_SUMMARY_DESCRIPTION = """Role Description: {role_description}
Task: {task}

Relevant Documents:
{documents}


Review and analyze the provided documents with respect to the task. Craft a concise and short, unified summary that distills key information that is most relevant to the task, incorporating reference links within the summary.
Only use the information given. Do not add any additional information. The summary should be less than {n} setences
"""  # noqa: E501


class ContextSearch(BaseRetrievalAction):
    role_description: str
    task: str
    llm: Any  # The BaseLanguageModel from LangChain is not compatible with Pydantic 2 yet
    description: str = SEARCH_SUMMARY_DESCRIPTION
    _context: Any

    # Override the name and args from BaseAction
    name: str = "Context Search"
    args: dict = {"query": "string"}
    usage: str = "Search the conversation history with the user"
    perform_refinement: bool = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._context = ContextTool(memory=get_vectordb())

    def search(self, query) -> str:
        resources = self._context._run(query, return_resources=True)

        self.add_resources(resources)

        # logger.debug("Context Search Result: {}", result)

        return resources

    def refine(self, result: str) -> str:
        prompt = self.description.format(
            task=self.task,
            documents=result,
            n=self.num_documents,
            role_description=self.role_description,
        )

        return self.llm.predict(prompt)
