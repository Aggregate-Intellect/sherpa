from typing import Any, Optional

from loguru import logger
from langchain_core.language_models.base import BaseLanguageModel

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
    """An action for searching and retrieving information from conversation context.
    
    This class provides functionality to search through conversation history and
    retrieve relevant information based on a query, with optional refinement of results.
    
    This class inherits from :class:`BaseRetrievalAction` and provides methods to:
      - Search conversation history for relevant information
      - Refine search results into concise summaries
      - Process and structure context information
    
    Attributes:
        role_description (str): Description of the role context for refinement.
        task (str): The specific task or question to focus on.
        llm (Any): Language model used for refining search results.
        description (str): Template for generating refinement prompts.
        _context (Any): Internal tool for accessing conversation context.
        name (str): Name of the action, set to "Context Search".
        args (dict): Arguments required by the action.
        usage (str): Description of the action's usage.
        perform_refinement (bool): Whether to refine search results. Defaults to True.
    
    Example:
        >>> search = ContextSearch(
        ...     role_description="AI assistant",
        ...     task="Find information about previous discussions",
        ...     llm=my_llm
        ... )
        >>> results = search.search("quantum computing")
        >>> summary = search.refine(results)
        >>> print(summary)
        Based on our previous discussions, quantum computing uses quantum bits...
    """
    
    role_description: str
    task: str
    llm: Optional[BaseLanguageModel] = None
    description: str = SEARCH_SUMMARY_DESCRIPTION
    _context: Any = None

    # Override the name and args from BaseAction
    name: str = "Context Search"
    args: dict = {"query": "string"}
    usage: str = "Search the conversation history with the user"
    perform_refinement: bool = True

    def __init__(self, **kwargs):
        """Initialize a ContextSearch action with the provided parameters.
        
        Args:
            **kwargs: Keyword arguments passed to the parent class.
        """
        super().__init__(**kwargs)
        self._context = ContextTool(memory=get_vectordb())

    def search(self, query) -> str:
        """Search conversation history for information relevant to the query.
        
        This method uses the ContextTool to search through conversation history
        and retrieve relevant information.
        
        Args:
            query (str): The search query.
            
        Returns:
            resources (str): Containing search results.
        """
        resources = self._context._run(query, return_resources=True)

        self.add_resources(resources)

        # logger.debug("Context Search Result: {}", result)

        return resources

    def refine(self, result: str) -> str:
        """Refine the search results into a concise summary.
        
        This method formats a prompt using the action's description template and
        the provided result, then uses the LLM to generate a refined summary.
        
        Args:
            result (str): The search results to be refined into a summary.
            
        Returns:
            str: A refined summary of the search results, focused on the specified task.
        """
        prompt = self.description.format(
            task=self.task,
            documents=result,
            n=self.num_documents,
            role_description=self.role_description,
        )
        return self.llm.invoke(prompt)
