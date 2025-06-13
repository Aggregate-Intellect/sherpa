from typing import Any, Optional

from loguru import logger
from langchain_core.language_models.base import BaseLanguageModel
from sherpa_ai.actions.base import BaseAction


PLANNING_PROMPT = """You are a **task decomposition assistant** who simplifies complex tasks into sequential steps, assigning roles or agents to each.
By analyzing user-defined tasks and agent capabilities, you provides structured plans, enhancing project clarity and efficiency.
Your adaptability ensures customized solutions for diverse needs.

A good plan is concise, detailed, feasible and efficient.

Task: **{task}**

Agents:
{agent_pool_description}

Please break down the task into maximum {num_steps} individual, detailed steps and designate an appropriate agent for each step. The result should be in the following format:
Step 1:
    Agent: <AgentName>
    Task: <detailed task description>
...
Step N:
    Agent: <AgentName>
    Task: <detailed task description>

Do not answer anything else, and do not add any other information in your answer. Only select agents from the the list and only select one agent at a time.
"""  # noqa: E501


REVISION_PROMPT = """You are a **task decomposition assistant** who simplifies complex tasks into sequential steps, assigning roles or agents to each.
By analyzing user-defined tasks and agent capabilities, you provide structured plans, enhancing project clarity and efficiency.
Your adaptability ensures customized solutions for diverse needs.

A good plan is concise, detailed, feasible and efficient. It should be broken down into individual steps, with each step assigned to an appropriate agent.

Task: **{task}**

Agents:
{agent_pool_description}

Here is your previous plan:
{previous_plan}

Here is the feedback from the last run:
{feedback}

Please revise the plan based on the feedback to maximum {num_steps} steps. The result should be in the following format:
Step 1:
    Agent: <AgentName>
    Task: <detailed task description>
...
Step N:
    Agent: <AgentName>
    Task: <detailed task description>

Do not answer anything else, and do not add any other information in your answer. Only select agents from the the list and only select one agent at a time.
"""  # noqa: E501


class Step:
    """A single step in a task execution plan.
    
    This class represents a single step in a plan, consisting of an agent assigned
    to perform a specific task.
    
    Attributes:
        agent_name (str): The name of the agent assigned to execute this step.
        task (str): The detailed description of the task to be executed.
    
    Example:
        >>> step = Step(agent_name="Researcher", task="Find information about quantum computing")
        >>> print(step)
        Agent: Researcher
        Task: Find information about quantum computing
    """

    def __init__(
        self,
        agent_name: str,
        task: str,
    ):
        """Initialize a Step with an agent and task.
        
        Args:
            agent_name (str): The name of the agent assigned to this step.
            task (str): The detailed description of the task to be executed.
        """
        self.agent_name = agent_name
        self.task = task

    def __str__(self) -> str:
        """Return a string representation of the step.
        
        Returns:
            str: A formatted string showing the agent and task.
        """
        return f"Agent: {self.agent_name}\nTask: {self.task}\n"

    @classmethod
    def from_dict(cls, data):
        """Create a Step instance from a dictionary.
        
        Args:
            data (dict): Dictionary containing 'agent_name' and 'task' keys.
            
        Returns:
            Step: A new Step instance with the provided data.
        """
        return cls(data["agent_name"], data["task"])


class Plan:
    """A collection of steps forming a complete task execution plan.
    
    This class represents a complete plan for executing a task, consisting of
    multiple steps, each assigned to a specific agent.
    
    Attributes:
        steps (list[Step]): List of steps in the plan.
    
    Example:
        >>> plan = Plan()
        >>> plan.add_step(Step("Researcher", "Find information"))
        >>> plan.add_step(Step("Writer", "Summarize findings"))
        >>> print(plan)
        Step 1:
        Agent: Researcher
        Task: Find information
        Step 2:
        Agent: Writer
        Task: Summarize findings
    """
    
    def __init__(self):
        """Initialize an empty plan."""
        self.steps = []

    def add_step(self, step: Step):
        """Add a step to the plan.
        
        Args:
            step (Step): The step to add to the plan.
        """
        self.steps.append(step)

    def __str__(self) -> str:
        """Return a string representation of the plan.
        
        Returns:
            str: A formatted string showing all steps in the plan.
        """
        result = ""
        for i, step in enumerate(self.steps):
            result += f"Step {i + 1}:\n{str(step)}"
        return result

    @property
    def __dict__(self):
        """Return a dictionary representation of the plan.
        
        Returns:
            dict: A dictionary containing the steps in the plan.
        """
        return {"steps": [step.__dict__ for step in self.steps]}

    @classmethod
    def from_dict(cls, data):
        """Create a Plan instance from a dictionary.
        
        Args:
            data (dict): Dictionary containing a 'steps' key with a list of step dictionaries.
            
        Returns:
            Plan: A new Plan instance with the provided steps.
        """
        plan = cls()
        plan.steps = [Step.from_dict(step) for step in data["steps"]]
        return plan


class TaskPlanning(BaseAction):
    """An action for creating and revising task execution plans.
    
    This class provides functionality to decompose complex tasks into sequential steps,
    assigning appropriate agents to each step. It can create new plans or revise
    existing plans based on feedback.
    
    This class inherits from :class:`BaseAction` and provides methods to:
      - Create new task execution plans
      - Revise existing plans based on feedback
      - Process and structure plan outputs
    
    Attributes:
        llm (Any): Language model used for generating plans.
        num_steps (int): Maximum number of steps in a plan. Defaults to 5.
        prompt (str): Template for generating new plans.
        revision_prompt (str): Template for revising existing plans.
        name (str): Name of the action, set to "TaskPlanning".
        args (dict): Arguments required by the action.
        usage (str): Description of the action's usage.
    
    Example:
        >>> planning = TaskPlanning(llm=my_llm)
        >>> plan = planning.execute(
        ...     task="Research quantum computing and write a summary",
        ...     agent_pool_description="Researcher: Finds information\nWriter: Creates summaries"
        ... )
        >>> print(plan)
        Step 1:
        Agent: Researcher
        Task: Find information about quantum computing
        Step 2:
        Agent: Writer
        Task: Summarize the findings about quantum computing
    """
    
    llm: Optional[BaseLanguageModel] = None
    num_steps: int = 5
    prompt: str = PLANNING_PROMPT
    revision_prompt: str = REVISION_PROMPT

    # Override the name and args from BaseAction
    name: str = "TaskPlanning"
    args: dict = {
        "task": "string",
        "agent_pool_description": "string",
        "last_plan": "string",
        "feedback": "string",
    }
    usage: str = "Come up with a plan to solve the task"

    def execute(
        self,
        task: str,
        agent_pool_description: str,
        last_plan: Optional[str] = None,
        feedback: Optional[str] = None,
    ) -> Plan:
        """Execute the task planning action.
        
        This method generates a new plan or revises an existing plan based on the
        provided task, agent pool, and optional feedback.
        
        Args:
            task (str): The task to be planned.
            agent_pool_description (str): Description of available agents and their capabilities.
            last_plan (Optional[str]): Previous plan to revise, if any.
            feedback (Optional[str]): Feedback on the previous plan, if any.
            
        Returns:
            Plan: A structured plan for executing the task.
        """
        if last_plan is None or feedback is None:
            prompt = self.prompt.format(
                task=task,
                agent_pool_description=agent_pool_description,
                num_steps=self.num_steps,
            )
        else:
            prompt = self.revision_prompt.format(
                task=task,
                agent_pool_description=agent_pool_description,
                previous_plan=last_plan,
                feedback=feedback,
                num_steps=self.num_steps,
            )

        logger.debug(f"Prompt: {prompt}")

        action_output = self.llm.invoke(prompt)

        return self.post_process(action_output)

    def post_process(self, action_output: str) -> Plan:
        """Process the raw output from the LLM into a structured Plan.
        
        This method parses the text output from the language model and converts it
        into a structured Plan object with Step objects.
        
        Args:
            action_output (str): Raw text output from the language model.
            
        Returns:
            Plan: A structured plan containing steps with assigned agents and tasks.
        """
        # print(action_output)
        steps = [step for step in action_output.split("Step") if step]
        plan = Plan()

        for step_str in steps:
            lines = step_str.strip()
            if len(lines) == 0:
                continue

            lines = lines.split("\n")

            # print(lines)
            agent_name = lines[1].split("Agent:")[1].strip()
            task_description = lines[2].split("Task:")[1].strip()

            plan.add_step(Step(agent_name, task_description))

        return plan
