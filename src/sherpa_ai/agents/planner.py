from typing import Optional

from loguru import logger

from sherpa_ai.prompts.prompt_template import PromptTemplate
from sherpa_ai.actions.planning import TaskPlanning
from sherpa_ai.agents.agent_pool import AgentPool
from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.events import EventType


template = PromptTemplate("./sherpa_ai/prompts/prompts.json")

planner_description = template.format_prompt(
            wrapper="planner_prompts",
            name="PLANNER_DESCRIPTION",
            version="1.0",
        )

class Planner(BaseAgent):
    name: str = "Planner"
    description: str = planner_description

    planning: TaskPlanning = None
    agent_pool: AgentPool
    num_runs: int = 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.planning = TaskPlanning(
            llm=self.llm,
            num_steps=self.num_runs,
        )

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
