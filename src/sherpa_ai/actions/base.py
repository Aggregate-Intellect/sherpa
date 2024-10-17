import json
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional, Union

from loguru import logger
from pydantic import BaseModel, Field

from sherpa_ai.actions.utils.refinement import BaseRefinement
from sherpa_ai.actions.utils.reranking import BaseReranking
from sherpa_ai.events import EventType

if TYPE_CHECKING:
    from sherpa_ai.memory.belief import Belief


class ActionResource(BaseModel):
    """
    Resource used for an action.

    Attributes:
        source (str): Source of the resource, such as document id or url.
        content (str): Content of the resource.
    """

    source: str
    content: str


class ActionArgument(BaseModel):
    """
    Argument used for an action.

    Attributes:
        name (str): Name of the argument.
        type (str): Type of the argument. (default: "str")
        description (str): Description of the argument. (default: "")
        source (str): source of the argument, select from (agent, belief)
            If source is agent, the argument is provided by the agent (LLM).
            If source is belief, the value of the argument is retrieved from the
            dictionary of the belief. (default: "agent")
        key (str): key of the argument in the belief dictionary if source is belief.
            (default: name of the argument, if source is belief)
    """

    name: str
    type: str = "str"
    description: str = ""
    source: str = "agent"
    key: Optional[str] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.source == "belief" and not self.key:
            self.key = self.name


class BaseAction(ABC, BaseModel):
    """
    Base class for an action.

    Attributes:
        name (str): Name of the action.
        args (Union[dict, list[ActionArgument]]): Arguments required to run the action.
        usage (str): Usage description of the action.
        belief (Any): Belief used for the action. It is required if any argument
            requires belief. (default: None)
        output_key (Optional[str]): Output key of the action. (default: name of the
            action)
    """

    class Config:
        arbitrary_types_allowed = True

    name: str
    args: Union[dict, list[ActionArgument]]
    usage: str
    belief: Any = None
    output_key: Optional[str] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._process_arguments()

        if self.output_key is None:
            self.output_key = self.name

    def _process_arguments(self):
        """
        Process the arguments for the action. Converting the arguments to list of
        ActionArgument if it is a dict. Check if belief is provided if any argument
        require belief.
        """
        if isinstance(self.args, dict):
            # convert dict to list of ActionArgument
            arguments = []
            for arg_name, arg_value in self.args.items():
                if isinstance(arg_value, str):
                    arg_value = {"type": arg_value}
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
    def execute(self, **kwargs):
        pass

    def __call__(self, **kwargs):
        # Retrieve the arguments from the belief or agent
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

        # Log to the belief
        if self.belief is not None:
            self.belief.update_internal(
                EventType.action, self.name, f"Action: {self.name} starts, Args: {filtered_kwargs}"
            )


        # Execute the action
        result = self.execute(**filtered_kwargs)

        # Save the result to the belief
        self.belief: Belief = self.belief
        if self.belief:
            self.belief.set(self.output_key, result)
            self.belief.update_internal(
                EventType.action_output, self.name, f"Action: {self.name} finishes, Observation: {result}"
            )

        return result

    def __str__(self):
        arguments = {}

        for arg in self.args:
            if arg.source != "agent":
                continue
            arguments[arg.name] = (
                arg.type if arg.description == "" else f"{arg.type}, {arg.description}"
            )

        tool_desc = {"name": self.name, "args": arguments, "usage": self.usage}

        return json.dumps(tool_desc, indent=4)

    def __repr__(self):
        return self.__str__()


class BaseRetrievalAction(BaseAction, ABC):
    resources: list[ActionResource] = Field(default_factory=list)
    num_documents: int = 5  # Number of documents to retrieve
    reranker: BaseReranking = None
    refiner: BaseRefinement = None
    current_task: str = ""

    perform_reranking: bool = False
    perform_refinement: bool = False

    def add_resources(self, resources: list[dict]):
        action_resources = self.resources
        action_resources.clear()

        for resource in resources:
            action_resources.append(
                ActionResource(source=resource["Source"], content=resource["Document"])
            )

    def execute(self, query: str) -> str:
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
    def search(self, query: str) -> str:
        """
        Search for relevant documents based on the query.
        """
        pass

    def reranking(self, documents: list[str]) -> list[str]:
        """
        Rerank the documents based on the query.
        """
        return self.reranker.rerank(documents, self.current_task)

    def refine(self, documents: list[str]) -> list[str]:
        """
        Refine the results based on the query.
        """
        return self.refiner.refinement(documents, self.current_task)
