import json
from typing import List

from langchain_core.tools import BaseTool

FINISH_NAME = "finish"


class PromptGenerator:
    """A class for generating structured prompt strings for AI agents.

    This class provides functionality to create well-structured prompts for AI agents
    by combining constraints, commands, resources, and performance evaluations. It
    generates prompts in a consistent format that can be easily parsed by the agent.

    This class provides methods to:
        - Add constraints to guide agent behavior
        - Add tools/commands the agent can use
        - Add resources available to the agent
        - Add performance evaluation criteria
        - Generate formatted prompt strings

    Attributes:
        constraints (List[str]): List of constraints that guide agent behavior.
        commands (List[BaseTool]): List of tools/commands available to the agent.
        resources (List[str]): List of resources available to the agent.
        performance_evaluation (List[str]): List of performance evaluation criteria.
        response_format (dict): JSON structure defining the expected response format.

    Example:
        >>> from sherpa_ai.prompt_generator import PromptGenerator
        >>> generator = PromptGenerator()
        >>> generator.add_constraint("Always be helpful")
        >>> generator.add_tool(tool)
        >>> prompt = generator.generate_prompt_string()
        >>> print(prompt)
        Constraints:
        1. Always be helpful
        ...
    """

    def __init__(self) -> None:
        """Initialize the PromptGenerator with empty lists and default response format.

        This method sets up the initial state of the PromptGenerator with empty lists
        for constraints, commands, resources, and performance evaluations, along with
        a default response format structure.

        Example:
            >>> generator = PromptGenerator()
            >>> print(len(generator.constraints))
            0
            >>> print(len(generator.commands))
            0
        """
        self.constraints: List[str] = []
        self.commands: List[BaseTool] = []
        self.resources: List[str] = []
        self.performance_evaluation: List[str] = []
        self.response_format = {
            "thoughts": {
                "text": "thought",
                # "reasoning": "reasoning",
                # "plan": "- short bulleted\n- list that conveys\n- long-term plan",
                # "criticism": "constructive self-criticism",
                "speak": "thoughts summary to say to user",
            },
            "command": {
                "name": "tool/command name you choose",
                "args": {"arg name": "value"},
            },
        }

    def add_constraint(self, constraint: str) -> None:
        """Add a constraint to guide the agent's behavior.

        Args:
            constraint (str): The constraint to be added to the list.

        Example:
            >>> generator = PromptGenerator()
            >>> generator.add_constraint("Always be helpful")
            >>> print(generator.constraints[0])
            Always be helpful
        """
        self.constraints.append(constraint)

    def add_tool(self, tool: BaseTool) -> None:
        """Add a tool/command that the agent can use.

        Args:
            tool (BaseTool): The tool to be added to the commands list.

        Example:
            >>> from langchain_core.tools import BaseTool
            >>> class MyTool(BaseTool):
            ...     name = "my_tool"
            ...     description = "A tool for testing"
            ...     def _run(self, query: str) -> str:
            ...         return "Result"
            >>> generator = PromptGenerator()
            >>> generator.add_tool(MyTool())
            >>> print(len(generator.commands))
            1
        """
        self.commands.append(tool)

    def _generate_command_string(self, tool: BaseTool) -> str:
        """Generate a formatted string representation of a tool/command.

        Args:
            tool (BaseTool): The tool to generate a string for.

        Returns:
            str: A formatted string containing the tool's name, description, and args schema.

        Example:
            >>> from langchain_core.tools import BaseTool
            >>> class MyTool(BaseTool):
            ...     name = "my_tool"
            ...     description = "A tool for testing"
            ...     args = {"query": "string"}
            ...     def _run(self, query: str) -> str:
            ...         return "Result"
            >>> generator = PromptGenerator()
            >>> string = generator._generate_command_string(MyTool())
            >>> print(string)
            my_tool: A tool for testing, args json schema: {"query": "string"}
        """
        output = f"{tool.name}: {tool.description}"
        output += f", args json schema: {json.dumps(tool.args)}"
        return output

    def add_resource(self, resource: str) -> None:
        """Add a resource that is available to the agent.

        Args:
            resource (str): The resource to be added to the resources list.

        Example:
            >>> generator = PromptGenerator()
            >>> generator.add_resource("Internet access")
            >>> print(generator.resources[0])
            Internet access
        """
        self.resources.append(resource)

    def add_performance_evaluation(self, evaluation: str) -> None:
        """Add a performance evaluation criterion for the agent.

        Args:
            evaluation (str): The evaluation criterion to be added to the list.

        Example:
            >>> generator = PromptGenerator()
            >>> generator.add_performance_evaluation("Be efficient")
            >>> print(generator.performance_evaluation[0])
            Be efficient
        """
        self.performance_evaluation.append(evaluation)

    def _generate_numbered_list(self, items: list, item_type: str = "list") -> str:
        """Generate a numbered list from given items based on the item_type.

        This method creates a formatted string with numbered items. For commands,
        it adds a special "finish" command at the end.

        Args:
            items (list): A list of items to be numbered.
            item_type (str, optional): The type of items in the list.
                Defaults to "list". Special handling for "command" type.

        Returns:
            str: The formatted numbered list as a string.

        Example:
            >>> generator = PromptGenerator()
            >>> items = ["item1", "item2"]
            >>> result = generator._generate_numbered_list(items)
            >>> print(result)
            1. item1
            2. item2
        """
        if item_type == "command":
            command_strings = [
                f"{i + 1}. {self._generate_command_string(item)}"
                for i, item in enumerate(items)
            ]
            finish_description = (
                "use this to signal that you have finished the current task"
            )
            finish_args = (
                '"response": "final response to let '
                'people know you have finished the current task"'
            )
            finish_string = (
                f"{len(items) + 1}. {FINISH_NAME}: "
                f"{finish_description}, args: {finish_args}"
            )
            return "\n".join(command_strings + [finish_string])
        else:
            return "\n".join(f"{i+1}. {item}" for i, item in enumerate(items))

    def generate_prompt_string(self) -> str:
        """Generate a complete prompt string for the agent.

        This method combines all constraints, commands, resources, and performance
        evaluations into a single formatted prompt string with the response format.

        Returns:
            str: The complete prompt string for the agent.

        Example:
            >>> generator = PromptGenerator()
            >>> generator.add_constraint("Always be helpful")
            >>> prompt = generator.generate_prompt_string()
            >>> print(prompt)
            Constraints:
            1. Always be helpful
            ...
        """
        formatted_response_format = json.dumps(self.response_format, indent=4)
        prompt_string = (
            f"Constraints:\n"
            f"{self._generate_numbered_list(self.constraints)}\n\n"
            f"Commands:\n"
            f"{self._generate_numbered_list(self.commands, item_type='command')}\n\n"
            # f"Resources:\n{self._generate_numbered_list(self.resources)}\n\n"
            f"Performance Evaluation:\n"
            f"{self._generate_numbered_list(self.performance_evaluation)}\n\n"
            f"You should only respond in JSON format as described below"
            " without any extra text."
            f"\nResponse Format: \n{formatted_response_format} "
            f"\nEnsure the response can be parsed by Python json.loads"
        )

        return prompt_string


def get_prompt(tools: List[BaseTool]) -> str:
    """Generate a complete prompt string with predefined constraints and evaluations.

    This function creates a PromptGenerator instance and populates it with standard
    constraints, tools, resources, and performance evaluations. It then generates
    and returns a complete prompt string.

    Args:
        tools (List[BaseTool]): List of tools/commands to include in the prompt.

    Returns:
        str: A complete prompt string with all components.

    Example:
        >>> from langchain_core.tools import BaseTool
        >>> class MyTool(BaseTool):
        ...     name = "my_tool"
        ...     description = "A tool for testing"
        ...     args = {"query": "string"}
        ...     def _run(self, query: str) -> str:
        ...         return "Result"
        >>> tools = [MyTool()]
        >>> prompt = get_prompt(tools)
        >>> print("Constraints:" in prompt)
        True
        >>> print("Commands:" in prompt)
        True
    """
    # Initialize the PromptGenerator object
    prompt_generator = PromptGenerator()

    prompt_generator.add_constraint(
        "If you are unsure how you previously did something "
        "or want to recall past events, "
        "thinking about similar events will help you remember."
    )
    prompt_generator.add_constraint(
        "You can seek for user assistance only by using the corresponding tool"
    )
    prompt_generator.add_constraint(
        'Exclusively use the commands listed in double quotes e.g. "command name"'
    )
    prompt_generator.add_constraint(
        'You must always choose a command unless you want to "finish"'
    )

    # Add commands to the PromptGenerator object
    for tool in tools:
        prompt_generator.add_tool(tool)

    # Add resources to the PromptGenerator object
    prompt_generator.add_resource(
        "Internet access for searches and information gathering."
    )
    prompt_generator.add_resource("Long Term memory management.")
    prompt_generator.add_resource(
        "GPT-3.5 powered Agents for delegation of simple tasks."
    )
    prompt_generator.add_resource("File output.")

    # Add performance evaluations to the PromptGenerator object
    prompt_generator.add_performance_evaluation(
        "Continuously review and analyze your actions "
        "to ensure you are performing to the best of your abilities."
    )
    prompt_generator.add_performance_evaluation(
        "Constructively self-criticize your big-picture behavior constantly."
    )
    prompt_generator.add_performance_evaluation(
        "Reflect on past decisions and strategies to refine your approach."
    )
    prompt_generator.add_performance_evaluation(
        "Every command has a cost, so be smart and efficient. "
        "Aim to complete tasks in the least number of steps."
    )

    # Generate the prompt string
    prompt_string = prompt_generator.generate_prompt_string()

    return prompt_string
