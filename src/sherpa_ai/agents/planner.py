from typing import Optional

from langchain_core.language_models import LLM 
from loguru import logger 

from sherpa_ai.actions.planning import TaskPlanning
from sherpa_ai.agents.agent_pool import AgentPool
from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.events import Event, EventType
from sherpa_ai.memory import Belief, SharedMemory
from sherpa_ai.verbose_loggers.verbose_loggers import DummyVerboseLogger


PLANNER_DESCRIPTION = """You are a **task decomposition assistant** who simplifies complex tasks into sequential steps, assigning roles or agents to each.
By analyzing user-defined tasks and agent capabilities, you provide structured plans, enhancing project clarity and efficiency.
Your adaptability ensures customized solutions for diverse needs.
"""  # noqa: E501


class Planner(BaseAgent):
    def __init__(
        self,
        agent_pool: AgentPool,
        name: str = "Planner",
        description: str = PLANNER_DESCRIPTION,
        shared_memory: SharedMemory = None,
        belief: Belief = None,
        action_selector=None,
        llm=LLM,
        num_steps: int = 5,
        verbose_logger=DummyVerboseLogger(),
    ):
        self.name = name
        self.description = description
        self.agent_pool = agent_pool
        self.shared_memory = shared_memory
        self.belief = belief
        self.action_selector = action_selector

        self.planning = TaskPlanning(
            llm=llm,
            num_steps=num_steps,
        )
        self.verbose_logger = verbose_logger

    def get_last_feedback(self) -> Optional[str]:
        """
        Get the last feedback from the shared memory
        """
        feedback_events = self.shared_memory.get_by_type(EventType.feedback)
        if len(feedback_events) == 0:
            return None
        else:
            return feedback_events[-1].content

    def get_last_plan(self) -> Optional[str]:
        """
        Get the last plan from the shared memory
        """
        plan_events = self.shared_memory.get_by_type(EventType.planning)
        if len(plan_events) == 0:
            return None
        else:
            return plan_events[-1].content

    def plan(self, task: str):
        """
        Plan the next action for the agent pool
        """
        agent_pool_description = self.agent_pool.get_agent_pool_description()
        feedback = self.get_last_feedback()
        last_plan = self.get_last_plan()

        # run the planning
        plan = self.planning.execute(task, agent_pool_description, last_plan, feedback)

        logger.info(f"Plan: {plan}")

        self.shared_memory.add(
            event_type=EventType.planning, agent=self.name, content=str(plan)
        )

        return plan

    def create_actions(self):
        pass

    def synthesize_output(self) -> str:
        pass
