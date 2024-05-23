from typing import Any, Optional

from loguru import logger

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
    """
    Step for the plan created by the planner
        agent_name: the name of the agent that should execute the step
        task: the task that the agent should execute
    """

    def __init__(
        self,
        agent_name: str,
        task: str,
    ):
        self.agent_name = agent_name
        self.task = task

    def __str__(self) -> str:
        return f"Agent: {self.agent_name}\nTask: {self.task}\n"

    @classmethod
    def from_dict(cls, data):
        return cls(data["agent_name"], data["task"])


class Plan:
    def __init__(self):
        self.steps = []

    def add_step(self, step: Step):
        self.steps.append(step)

    def __str__(self) -> str:
        result = ""
        for i, step in enumerate(self.steps):
            result += f"Step {i + 1}:\n{str(step)}"
        return result

    @property
    def __dict__(self):
        return {"steps": [step.__dict__ for step in self.steps]}

    @classmethod
    def from_dict(cls, data):
        plan = cls()
        plan.steps = [Step.from_dict(step) for step in data["steps"]]
        return plan


class TaskPlanning(BaseAction):
    llm: Any  # The BaseLanguageModel from LangChain is not compatible with Pydantic 2 yet
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
        """
        Execute the action
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

        action_output = self.llm.predict(prompt)

        return self.post_process(action_output)

    def post_process(self, action_output: str) -> Plan:
        """
        Post process the action output into a plan with steps
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
