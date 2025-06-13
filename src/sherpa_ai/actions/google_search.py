from typing import Any, Optional

from loguru import logger
from langchain_core.language_models.base import BaseLanguageModel
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
    """A class for searching and retrieving information from Google Search.
    
    This class provides functionality to search for information on Google based on a query,
    retrieve relevant results, and refine them using an LLM to create concise summaries.
    
    This class inherits from :class:`BaseRetrievalAction` and provides methods to:
      - Search for information on Google using a query
      - Refine search results into concise summaries relevant to a specific task
      - Extract original sentences from search results when needed
    
    Attributes:
        role_description (str): Description of the role context for refining results.
        task (str): The specific task or question to focus on when refining results.
        llm (Any): Language model used for refining search results.
        description (str): Template for generating refinement prompts.
        config (AgentConfig): Configuration for the search agent.
        _search_tool (Any): Internal tool for performing Google searches.
        name (str): Name of the action, set to "Google Search".
        args (dict): Arguments accepted by the action, including "query".
        usage (str): Description of the action's usage.
    
    Example:
        >>> from sherpa_ai.actions import GoogleSearch
        >>> search = GoogleSearch(
        ...     role_description="Research assistant",
        ...     task="Find information about quantum computing"
        ... )
        >>> results = search.search("quantum computing applications")
        >>> summary = search.refine(results)
        >>> print(summary)
    """
    role_description: str
    task: str
    llm: Optional[BaseLanguageModel] = None
    description: str = SEARCH_SUMMARY_DESCRIPTION
    config: AgentConfig = AgentConfig()
    _search_tool: Any = None

    # Override the name and args from BaseAction
    name: str = "Google Search"
    args: dict = {"query": "string"}
    usage: str = "Get answers from Google Search"

    def __init__(self, **kwargs):
        """Initialize the GoogleSearch action.
        
        Args:
            **kwargs: Additional keyword arguments for the action.
        """
        super().__init__(**kwargs)
        self._search_tool = SearchTool(config=self.config, top_k=self.num_documents)

    def search(self, query) -> list[dict]:
        """Search for relevant documents based on the query.
        
        This method performs a Google search and returns the top results.
        
        Args:
            query (str): The search query.

        Returns:
            list[dict]: List of dictionaries containing search results with "Source" and "Document" keys.
        """
        resources = self._search_tool._run(query, return_resources=True)
        self.add_resources(resources)

        return resources
