from langchain.base_language import BaseLanguageModel
from loguru import logger

from sherpa_ai.actions.base import ActionResource, BaseAction
from sherpa_ai.config.task_config import AgentConfig
from sherpa_ai.tools import SearchTool

# TODO check for prompt that keep orginal snetnences
SEARCH_SUMMARY_DESCRIPTION = """Role Description: {role_description}
Task: {task}

Relevant Documents:
{documents}


Review and analyze the provided documents with respect to the task. Craft a concise and short, unified summary that distills key information that is most relevant to the task, incorporating reference links within the summary.
Only use the information given. Do not add any additional information. The summary should be less than {n} setences
"""  # noqa: E501

SEARCH_EXTRACT_DESCRIPTION = """Role Description: {role_description}
Task: {task}

Relevant Documents:
{documents}


Review and analyze the provided documents with respect to the task. Extract original sentences from the relevant documents that is most relevant to the task, incorporating reference links within the summary.
Only use the information given. Do not add any additional information. The summary should be less than {n} setences.
"""  # noqa: E501


class GoogleSearch(BaseAction):
    def __init__(
        self,
        role_description: str,
        task: str,
        llm: BaseLanguageModel,
        description: str = SEARCH_SUMMARY_DESCRIPTION,
        config: AgentConfig = AgentConfig(),
        n: int = 5,
    ):
        self.role_description = role_description
        self.task = task

        self.description = description
        self.llm = llm
        self.n = n

        self.search_tool = SearchTool(config=config)
        self.action_resources = []

    def execute(self, query) -> str:
        result, resources = self.search_tool._run(query, return_resources=True)
        self.add_resources(resources)

        logger.debug("Search Result: {}", result)

        return result

    @property
    def name(self) -> str:
        return "Google Search"

    @property
    def args(self) -> dict:
        return {"query": "string"}

    @property
    def resources(self) -> list[ActionResource]:
        return self.action_resources
