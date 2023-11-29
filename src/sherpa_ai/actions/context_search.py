from langchain.base_language import BaseLanguageModel
from loguru import logger

from sherpa_ai.actions.base import BaseAction
from sherpa_ai.connectors.vectorstores import get_vectordb
from sherpa_ai.tools import ContextTool

SEARCH_SUMMARY_DESCRIPTION = """Role Description: {role_description}
Task: {task}

Relevant Documents:
{documents}


Review and analyze the provided documents with respect to the task. Craft a concise and short, unified summary that distills key information that is most relevant to the task, incorporating reference links within the summary.
Only use the information given. Do not add any additional information. The summary should be less than {n} setences
"""  # noqa: E501


class ContextSearch(BaseAction):
    def __init__(
        self,
        role_description: str,
        task: str,
        llm: BaseLanguageModel,
        description: str = SEARCH_SUMMARY_DESCRIPTION,
        n: int = 5,
    ):
        self.role_description = role_description
        self.task = task

        self.description = description
        self.llm = llm
        self.n = n

        self.context = ContextTool(memory=get_vectordb())

    def execute(self, query) -> str:
        result, metadata = self.context._run(query)
        # result = "Context Search"
        logger.debug("Context Search Result: {}", result)

        prompt = self.description.format(
            task=self.task,
            documents=result,
            n=self.n,
            role_description=self.role_description,
        )

        result = self.llm.predict(prompt)

        return result

    @property
    def name(self) -> str:
        return "Context Search"

    @property
    def args(self) -> dict:
        return {"query": "string"}
