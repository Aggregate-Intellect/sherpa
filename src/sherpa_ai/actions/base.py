import json
from abc import ABC, abstractmethod
from typing import Any, Optional, Union

from loguru import logger
from pydantic import BaseModel, ConfigDict, Field

from sherpa_ai.actions.exceptions import SherpaActionExecutionException
from sherpa_ai.actions.utils.refinement import BaseRefinement
from sherpa_ai.actions.utils.reranking import BaseReranking
from sherpa_ai.memory import Belief, SharedMemory
from sherpa_ai.prompts.prompt_template_loader import PromptTemplate


class ActionResource(BaseModel):
    """A model representing a resource used by an action.

    This class defines the structure for resources that can be used by actions,
    such as documents, URLs, or other content sources.

    Attributes:
        source (str): Source identifier of the resource, such as document ID or URL.
        content (str): The actual content of the resource.

    Example:
        >>> resource = ActionResource(source="doc123", content="This is the document content")
        >>> print(resource.source)
        doc123
    """  # noqa: E501

    source: str
    content: str


class ActionArgument(BaseModel):
    """A model representing an argument used by an action.

    This class defines the structure for arguments that can be passed to actions,
    including their type, description, and source.

    Attributes:
        name (str): Name of the argument.
        type (str): Data type of the argument. Defaults to "str".
        description (str): Description of what the argument represents. Defaults to "".
        source (str): Source of the argument value, either "agent" or "belief".
            If "agent", the argument is provided by the agent (LLM).
            If "belief", the value is retrieved from the belief dictionary. Defaults to "agent".
        key (Optional[str]): Key in the belief dictionary if source is "belief".
            Defaults to the argument name if not specified.

    Example:
        >>> arg = ActionArgument(name="query", type="str", description="Search query")
        >>> print(arg.name)
        query
    """  # noqa: E501

    name: str
    type: str = "str"
    description: str = ""
    source: str = "agent"
    key: Optional[str] = None

    def __init__(self, *args, **kwargs):
        """Initialize an ActionArgument with the provided parameters.

        If the source is "belief" and no key is provided, the key will be set to the argument name.

        Args:
            *args: Positional arguments passed to the parent class.
            **kwargs: Keyword arguments passed to the parent class.
        """  # noqa: E501
        super().__init__(*args, **kwargs)
        if self.source == "belief" and not self.key:
            self.key = self.name


class BaseAction(ABC, BaseModel):
    """Base class for all actions in the Sherpa AI system.

    This abstract class provides the foundation for all actions, defining the common
    interface and functionality that all actions must implement. It handles argument
    processing, validation, execution, and result management.

    This class inherits from :class:`ABC` and :class:`BaseModel` and provides methods to:
      - Process and validate action arguments
      - Execute actions with proper error handling
      - Manage action lifecycle (start, execution, end)
      - Store and retrieve results in the belief system

    Attributes:
        name (str): Unique identifier for the action.
        args (Union[dict, list[ActionArgument]]): Arguments required to run the action.
        usage (str): Description of how to use the action.
        belief (Belief): Belief system used for storing and retrieving information.
        output_key (Optional[str]): Key used to store the action result in the belief system.
        prompt_template (Optional[PromptTemplate]): Template for generating prompts.

    Example:
        >>> class MyAction(BaseAction):
        ...     name = "my_action"
        ...     args = {"input": "string"}
        ...     usage = "Performs a specific task"
        ...     def execute(self, **kwargs):
        ...         return f"Processed: {kwargs['input']}"
        >>> action = MyAction()
        >>> result = action(input="test")
        >>> print(result)
        Processed: test
    """  # noqa: E501

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    args: Union[dict, list[ActionArgument]]
    usage: str
    belief: Belief = None
    shared_memory: SharedMemory = None
    output_key: Optional[str] = None

    prompt_template: Optional[PromptTemplate] = None

    if prompt_template is None:
        prompt_template = PromptTemplate("prompts/prompts.json")

    def __init__(self, *args, **kwargs):
        """Initialize a BaseAction with the provided parameters.

        Args:
            *args: Positional arguments passed to the parent class.
            **kwargs: Keyword arguments passed to the parent class.
        """
        super().__init__(*args, **kwargs)
        self._process_arguments()

        if self.output_key is None:
            self.output_key = self.name

    def _process_arguments(self):
        """Process and validate the arguments for the action.

        This method converts dictionary arguments to ActionArgument objects and
        verifies that belief is provided when required by any argument.

        Raises:
            ValueError: If an argument requires belief but no belief is provided.
        """
        if isinstance(self.args, dict):
            # convert dict to list of ActionArgument
            arguments = []
            for arg_name, arg_value in self.args.items():
                if isinstance(arg_value, str):
                    arg_value = {"description": arg_value}
                arg_value["name"] = arg_name
                arguments.append(ActionArgument(**arg_value))
            self.args = arguments

        require_belief = False
        for arg in self.args:
            if arg.source == "belief":
                require_belief = True
                break

        if require_belief and not self.belief:
            raise ValueError(
                f"Action {self.name} requires belief but no belief is provided"
            )

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """Execute the action with the provided arguments.

        This method must be implemented by all subclasses to define the specific
        behavior of the action.

        Args:
            **kwargs: Keyword arguments required by the action.

        Returns:
            Any: The result of the action execution.
        """
        pass

    def input_validation(self, **kwargs) -> dict:
        """Validate and filter the input arguments for the action.

        This method checks that all required arguments are provided and retrieves
        values from the belief system when needed.

        Args:
            **kwargs: Keyword arguments to validate.

        Returns:
            dict: Filtered dictionary containing only the valid arguments.

        Raises:
            ValueError: If a required argument is missing or has an invalid source.
        """
        filtered_kwargs = {}
        for arg in self.args:
            if arg.source == "agent":
                if arg.name not in kwargs:
                    raise ValueError(f"Missing argument from input: {arg.name}")
                filtered_kwargs[arg.name] = kwargs[arg.name]
            elif arg.source == "belief":
                if not self.belief.has(arg.key):
                    raise ValueError(f"Missing argument in belief: {arg.name}")
                filtered_kwargs[arg.name] = self.belief.get(arg.key)
            else:
                raise ValueError(
                    f"Invalid source: {arg.source}, the available sources "
                    "are 'agent' and 'belief'"
                )

        return filtered_kwargs

    def action_start(self, args: dict):
        """Log the start of an action execution in the belief system.

        Args:
            args (dict): Arguments passed to the action.
        """
        if self.belief is not None:
            self.belief.update_internal("action_start", self.name, args=args)

    def action_end(self, result: Any):
        """Log the end of an action execution and store the result in the belief system.

        Args:
            result (Any): The result of the action execution.
        """
        if self.belief is not None:
            self.belief.set(self.output_key, result)
            self.belief.update_internal("action_finish", self.name, outputs=result)

    def __call__(self, **kwargs) -> Any:
        """Execute the action with the provided arguments.

        This method handles the complete lifecycle of an action execution:
        1. Validates the input arguments
        2. Logs the start of the action
        3. Executes the action
        4. Logs the end of the action and stores the result

        Args:
            **kwargs: Keyword arguments required by the action.

        Returns:
            Any: The result of the action execution.
        """
        # Retrieve the arguments from the belief or agent
        filtered_kwargs = self.input_validation(**kwargs)

        # Log to the belief
        self.action_start(filtered_kwargs)

        # Execute the action
        result = self.execute(**filtered_kwargs)

        # Save the result to the belief
        self.action_end(result)

        return result

    def __str__(self):
        """Return a string representation of the action.

        Returns:
            str: JSON string containing the action name, arguments, and usage.
        """
        arguments = {}
        for arg in self.args:
            if arg.source != "agent":
                continue
            arguments[arg.name] = (
                arg.type
                if arg.description == ""
                else f"{arg.description}. Type: {arg.type}"
            )

        tool_desc = {"name": self.name, "args": arguments, "usage": self.usage}

        return json.dumps(tool_desc, indent=4)

    def __repr__(self):
        """Return a string representation of the action.

        Returns:
            str: The same as __str__.
        """
        return self.__str__()


class AsyncBaseAction(BaseAction, ABC):
    """Base class for asynchronous actions in the Sherpa AI system.

    This class extends BaseAction to provide asynchronous execution capabilities,
    allowing actions to be executed without blocking the main thread.

    This class inherits from :class:`BaseAction` and provides methods to:
      - Execute actions asynchronously
      - Handle asynchronous action lifecycle

    Example:
        >>> class MyAsyncAction(AsyncBaseAction):
        ...     name = "my_async_action"
        ...     args = {"input": "string"}
        ...     usage = "Performs an asynchronous task"
        ...     async def execute(self, **kwargs):
        ...         # Simulate async work
        ...         await asyncio.sleep(1)
        ...         return f"Processed: {kwargs['input']}"
        >>> action = MyAsyncAction()
        >>> result = await action(input="test")
        >>> print(result)
        Processed: test
    """

    async def __call__(self, **kwargs):
        """Execute the action asynchronously with the provided arguments.

        This method handles the complete lifecycle of an asynchronous action execution:
        1. Validates the input arguments
        2. Logs the start of the action
        3. Executes the action asynchronously
        4. Logs the end of the action and stores the result

        Args:
            **kwargs: Keyword arguments required by the action.

        Returns:
            Any: The result of the action execution.
        """
        # Retrieve the arguments from the belief or agent
        filtered_kwargs = self.input_validation(**kwargs)

        # Log to the belief
        self.action_start(filtered_kwargs)

        # Execute the action
        result = await self.execute(**filtered_kwargs)

        # Save the result to the belief
        self.action_end(result)

        return result

    @abstractmethod
    async def execute(self, **kwargs):
        """Execute the action asynchronously with the provided arguments.

        This method must be implemented by all subclasses to define the specific
        behavior of the asynchronous action.

        Args:
            **kwargs: Keyword arguments required by the action.

        Returns:
            Any: The result of the action execution.
        """
        return await self.execute(**kwargs)


class BaseRetrievalAction(BaseAction, ABC):
    """Base class for retrieval-based actions in the Sherpa AI system.

    This class extends BaseAction to provide functionality for retrieving and processing
    documents or resources based on a query. It supports reranking and refinement of
    search results.

    This class inherits from :class:`BaseAction` and provides methods to:
      - Search for relevant documents
      - Rerank search results
      - Refine search results
      - Manage document resources

    Attributes:
        resources (list[ActionResource]): List of resources retrieved by the action.
        num_documents (int): Number of documents to retrieve. Defaults to 5.
        reranker (BaseReranking): Component for reranking search results.
        refiner (BaseRefinement): Component for refining search results.
        current_task (str): Current task context for reranking and refinement.
        perform_reranking (bool): Whether to perform reranking on search results.
        perform_refinement (bool): Whether to perform refinement on search results.

    Example:
        >>> class MySearchAction(BaseRetrievalAction):
        ...     name = "my_search"
        ...     args = {"query": "string"}
        ...     usage = "Searches for documents"
        ...     def search(self, query):
        ...         # Implement search logic
        ...         return [{"Source": "doc1", "Document": "content1"}]
        >>> action = MySearchAction()
        >>> result = action(query="test")
        >>> print(result)
        content1
    """

    resources: list[ActionResource] = Field(default_factory=list)
    num_documents: int = 5  # Number of documents to retrieve
    reranker: BaseReranking = None
    refiner: BaseRefinement = None
    current_task: str = ""

    perform_reranking: bool = False
    perform_refinement: bool = False

    def add_resources(self, resources: list[dict]):
        """Add resources to the action's resource collection.

        This method clears the existing resources and adds the new ones.

        Args:
            resources (list[dict]): List of resource dictionaries with "Source" and "Document" keys.
        """  # noqa: E501
        action_resources = self.resources
        action_resources.clear()

        for resource in resources:
            action_resources.append(
                ActionResource(source=resource["Source"], content=resource["Document"])
            )

    def execute(self, query: str) -> str:
        """Execute the retrieval action with the provided query.

        This method performs the search, optionally reranks and refines the results,
        and returns the final processed results.

        Args:
            query (str): The search query.

        Returns:
            str: The processed search results as a string.

        Raises:
            SherpaActionExecutionException: If the query is empty.
        """  # noqa: E501
        if query is None or len(query) == 0:
            raise SherpaActionExecutionException("Query cannot be empty")

        results = self.search(query)

        results = [result["Document"] for result in results]

        if self.perform_reranking:
            results = self.reranking(results)
        if self.perform_refinement:
            results = self.refine(results)
        results = "\n\n".join(results)
        logger.debug("Action Results: {}", results)

        return results

    @abstractmethod
    def search(self, query: str) -> list[dict]:
        """Search for relevant documents based on the query.

        This method must be implemented by all subclasses to define the specific
        search behavior.

        Args:
            query (str): The search query.

        Returns:
            list[dict]: List of dictionaries containing search results with "Source" and "Document" keys.
        """  # noqa: E501
        pass

    def reranking(self, documents: list[str]) -> list[str]:
        """Rerank the documents based on the current task.

        Args:
            documents (list[str]): List of document contents to rerank.

        Returns:
            list[str]: Reranked list of document contents.
        """  # noqa: E501
        return self.reranker.rerank(documents, self.current_task)

    def refine(self, documents: list[str]) -> str:
        """Refine the search results based on the current task.

        Args:
            documents (list[str]): List of document contents to refine.

        Returns:
            str: Refined search results as a string.
        """
        return self.refiner.refinement(documents, self.current_task)
