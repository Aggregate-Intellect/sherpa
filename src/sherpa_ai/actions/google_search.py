from langchain.base_language import BaseLanguageModel
from loguru import logger

from sherpa_ai.actions.base import BaseAction
from sherpa_ai.config.task_config import AgentConfig
from sherpa_ai.tools import SearchTool

SEARCH_SUMMARY_DESCRIPTION = """Role Description: {role_description}
Task: {task}

Relevant Documents:
{documents}


Review and analyze the provided documents with respect to the task. Craft a concise and short, unified summary that distills key information that is most relevant to the task, incorporating reference links within the summary.
Only use the information given. Do not add any additional information. The summary should be less than {n} setences
"""  # noqa: E501


class GoogleSearch(BaseAction):
    def __init__(
        self,
        role_description: str,
        task: str,
        llm: BaseLanguageModel,
        config: AgentConfig,
        description: str = SEARCH_SUMMARY_DESCRIPTION,
        n: int = 5,
    ):
        self.role_description = role_description
        self.task = task

        self.description = description
        self.llm = llm
        self.n = n
        self.config = config

        self.search_tool = SearchTool()

    def config_gsite_query(self, query) -> str:
        # check if the gsite is none
        if self.config.gsite:
            query = query + " site:" + self.config.gsite
        return query

    def execute(self, query) -> str:
        query = self.config_gsite_query(query)
        result = self.search_tool._run(query)

        logger.debug("Search Result: {}", result)

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
        return "Google Search"

    @property
    def args(self) -> dict:
        return {"query": "string"}
