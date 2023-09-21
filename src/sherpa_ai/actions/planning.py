from typing import List

from langchain.llms.base import LLM

from sherpa_ai.actions.base import BaseAction

PLANNING_PROMPT = """You are a **task decomposition assisstant** who simplifies complex tasks into sequential steps, assigning roles or agents to each.
By analyzing user-defined tasks and agent capabilities, you provides structured plans, enhancing project clarity and efficiency.
Your adaptability ensures customized solutions for diverse needs.


Task: **{task}**

Agents:
{agent_pool_description}

Please break down the task into individual, detailed steps and designate an appropriate agent for each step. The result should be in the following format:
Step 1:
    Agent: <AgentName>
    Task: <detailed task description>
...
Step N:
    Agent: <AgentName>
    Task: <detailed task description>

Do not answer anything else, and do not add any other information in your answer.
"""  # noqa: E501


class Step:
    """
    Step for the plan created by the planner
        agent_name: the name of the agent that should execute the step
        task: the task that the agent should execute
    """

    def __init__(self, agent_name: str, task: str):
        self.agent_name = agent_name
        self.task = task

    def __str__(self) -> str:
        return f"Agent: {self.agent_name}\nTask: {self.task}\n"


class Plan:
    def __init__(self):
        self.steps = []

    def add_step(self, step: Step):
        self.steps.append(step)

    def __str__(self) -> str:
        result = ""
        for i, step in enumerate(self.steps):
            result += f"Step {i + 1}:\n{step}"


class TaskPlanning(BaseAction):
    def __init__(self, llm: LLM):
        self.llm = llm

        # TODO: define the prompt for planning, it take one arg (task,
        #  agent_pool_description)
        self.prompt = PLANNING_PROMPT

    def execute(self, task: str, agent_pool_description: str) -> Plan:
        """
        Execute the action
        """
        action_output = self.llm(self.prompt.format(task, agent_pool_description))

        return self.post_process(action_output)

    def post_process(self, action_output: str) -> Plan:
        """
        Post process the action output into a plan with steps
        """
        steps = [step for step in action_output.split("Step") if step]
        plan = Plan()

        for step_str in steps:
            lines = step_str.strip().split("\n")

            agent_name = lines[1].split("Agent:")[1].strip()
            task_description = lines[2].split("Task:")[1].strip()

            plan.add_step(Step(agent_name, task_description))

        return plan
