from typing import Any

from loguru import logger

from sherpa_ai.actions.base import BaseRetrievalAction
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


class GoogleSearch(BaseRetrievalAction):
    role_description: str
    task: str
    llm: Any  # The BaseLanguageModel from LangChain is not compatible with Pydantic 2 yet
    description: str = SEARCH_SUMMARY_DESCRIPTION
    config: AgentConfig = AgentConfig()
    _search_tool: Any

    # Override the name and args from BaseAction
    name: str = "Google Search"
    args: dict = {"query": "string"}
    usage: str = "Get answers from Google Search"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._search_tool = SearchTool(config=self.config, top_k=self.num_documents)

    def search(self, query) -> list[dict]:
        resources = self._search_tool._run(query, return_resources=True)
        self.add_resources(resources)

        return resources
