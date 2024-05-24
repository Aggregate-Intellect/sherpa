from langchain.base_language import BaseLanguageModel

from sherpa_ai.actions.base import ActionResource, BaseAction
from sherpa_ai.tools import SearchArxivTool


SEARCH_SUMMARY_DESCRIPTION = """Role Description: {role_description}
Task: {task}

Relevant Paper Title and Summary:
{paper_title_summary}


Review and analyze the provided paper summary with respect to the task. Craft a concise and short, unified summary that distills key information that is most relevant to the task, incorporating reference links within the summary.
Only use the information given. Do not add any additional information. The summary should be less than {n} setences
"""  # noqa: E501


class ArxivSearch(BaseAction):
    def __init__(
        self,
        role_description: str,
        task: str,
        llm: BaseLanguageModel,
        description: str = SEARCH_SUMMARY_DESCRIPTION,
        max_results: int = 5,
        action_usage: str = "Search paper on the Arxiv website",
    ):
        self.role_description = role_description
        self.task = task

        self.description = description
        self.llm = llm
        self.max_results = max_results
        self.action_resources = []

        self.search_tool = SearchArxivTool()
        self.action_usage = action_usage

    def execute(self, query) -> str:
        result, resources = self.search_tool._run(query, return_resources=True)
        self.add_resources(resources)

        prompt = self.description.format(
            task=self.task,
            paper_title_summary=result,
            n=self.max_results,
            role_description=self.role_description,
        )

        result = self.llm.predict(prompt)

        return result

    @property
    def name(self) -> str:
        return "ArxivSearch"

    @property
    def args(self) -> dict:
        return {"query": "string"}

    @property
    def usage(self) -> str:
        return self.action_usage

    @property
    def resources(self) -> list:
        return self.action_resources
