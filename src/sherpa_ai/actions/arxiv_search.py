from typing import Any, Optional
from langchain_core.language_models.base import BaseLanguageModel
from sherpa_ai.actions.base import BaseRetrievalAction
from sherpa_ai.tools import SearchArxivTool


SEARCH_SUMMARY_DESCRIPTION = """Role Description: {role_description}
Task: {task}

Relevant Paper Title and Summary:
{paper_title_summary}


Review and analyze the provided paper summary with respect to the task. Craft a concise and short, unified summary that distills key information that is most relevant to the task, incorporating reference links within the summary.
Only use the information given. Do not add any additional information. The summary should be less than {n} setences
"""  # noqa: E501


class ArxivSearch(BaseRetrievalAction):
    """A class for searching and retrieving papers from the Arxiv website.
    
    This class provides functionality to search for academic papers on Arxiv based on a query,
    retrieve relevant information, and refine the results using an LLM to create concise summaries.
    
    This class inherits from :class:`BaseRetrievalAction` and provides methods to:
      - Search for papers on Arxiv using a query
      - Refine search results into concise summaries relevant to a specific task
    
    Attributes:
      role_description (str): Description of the role context for refining results.
      task (str): The specific task or question to focus on when refining results.
      llm (Any): Language model used for refining search results.
      description (str): Template for generating refinement prompts.
      _search_tool (Any): Internal tool for performing Arxiv searches.
      name (str): Name of the action, set to "ArxivSearch".
      args (dict): Arguments accepted by the action, including "query".
      usage (str): Description of the action's usage.
      perform_refinement (bool): Whether to refine search results, default is True.
    
    Example:
      >>> from sherpa_ai.actions import ArxivSearch
      >>> search = ArxivSearch(role_description="AI researcher", task="Find papers on transformer architecture")
      >>> results = search.search("transformer architecture")
      >>> summary = search.refine(results)
      >>> print(summary)
    """
    role_description: str
    task: str
    llm: Optional[BaseLanguageModel] = None
    description: str = SEARCH_SUMMARY_DESCRIPTION
    _search_tool: Any = None

    # Override the name and args from BaseAction
    name: str = "ArxivSearch"
    args: dict = {"query": "string"}
    usage: str = "Search paper on the Arxiv website"
    perform_refinement: bool = True

    def __init__(self, **kwargs):
        """Initialize the ArxivSearch action with the provided parameters.
        
        Args:
            **kwargs: Keyword arguments passed to the parent class and used to set instance attributes.
        """
        super().__init__(**kwargs)
        self._search_tool = SearchArxivTool()

    def search(self, query) -> list[dict]:
        """Search for papers on Arxiv based on the provided query.
        
        This method uses the SearchArxivTool to find papers matching the query,
        adds the found resources to the action's resource collection, and returns them.
        
        Args:
            query (str): The search query to find relevant papers.
            
        Returns:
            list[dict]: A list of dictionaries containing information about found papers.
        """
        resources = self._search_tool._run(query, return_resources=True)
        self.add_resources(resources)

        return resources

    def refine(self, result: str) -> str:
        """Refine the search results into a concise summary relevant to the specified task.
        
        This method formats a prompt using the action's description template and the provided result,
        then uses the LLM to generate a refined summary that focuses on information relevant to the task.
        
        Args:
            result (str): The search results to be refined into a summary.
            
        Returns:
            str: A refined summary of the search results, focused on the specified task.
        """
        prompt = self.description.format(
            task=self.task,
            paper_title_summary=result,
            n=self.num_documents,
            role_description=self.role_description,
        )
        return self.llm.invoke(prompt)
