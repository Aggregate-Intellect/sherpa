from typing import Any, Optional
from langchain_core.language_models.base import BaseLanguageModel
from sherpa_ai.actions.base import BaseAction


DELIBERATION_DESCRIPTION = """Role Description: {role_description}
Task Description: {task}

Please deliberate on the task and generate a solution that is:

Highly Detailed: Break down components and elements clearly.
Quality-Oriented: Ensure top-notch performance and longevity.
Precision-Focused: Specific measures, materials, or methods to be used.

Keep the result concise and short. No more than one paragraph.

"""  # noqa: E501


class Deliberation(BaseAction):
    """A class for generating detailed and well-thought-out solutions to tasks.
    
    This class provides functionality to analyze tasks and generate comprehensive solutions
    that are detailed, quality-oriented, and precision-focused. It uses an LLM to deliberate
    on the task and produce a concise yet thorough response.
    
    This class inherits from :class:`BaseAction` and provides methods to:
      - Analyze and break down task components
      - Generate detailed solutions with specific measures and methods
      - Ensure quality and precision in the output
    
    Attributes:
        role_description (str): Description of the role context for deliberation.
        llm (Any): Language model used for generating solutions.
        description (str): Template for generating deliberation prompts.
        name (str): Name of the action, set to "Deliberation".
        args (dict): Arguments accepted by the action, including "task".
        usage (str): Description of the action's usage.
    
    Example:
        >>> from sherpa_ai.actions import Deliberation
        >>> deliberation = Deliberation(
        ...     role_description="Expert problem solver",
        ...     llm=my_llm
        ... )
        >>> solution = deliberation.execute(
        ...     task="Design a robust error handling system"
        ... )
        >>> print(solution)
    """
    # TODO: Make a version of Deliberation action that considers the context
    role_description: str
    llm: Optional[BaseLanguageModel] = None
    description: str = DELIBERATION_DESCRIPTION

    # Override the name and args from BaseAction
    name: str = "Deliberation"
    args: dict = {"task": "string"}
    usage: str = "Directly come up with a solution"

    def execute(self, task: str) -> str:
        """Execute the Deliberation action.

        Args:
            task (str): The task to deliberate on.

        Returns:
            str: The solution to the task.

        Raises:
            SherpaActionExecutionException: If the action fails to execute.
        """
        prompt = self.description.format(
            task=task, role_description=self.role_description
        )

        result = self.llm.invoke(prompt)

        return result
