from langchain.llms.base import LLM

from sherpa_ai.actions.planning import TaskPlanning
from sherpa_ai.agents.agent_pool import AgentPool
from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.memory.events import EventType


class Planner(BaseAgent):
    def __init__(
        self,
        name: str,
        description: str,
        agent_pool: AgentPool,
        shared_memory=None,
        belief=None,
        action_selector=None,
        num_runs=1,
        llm=LLM,
    ):
        # TODO: Define agent actions (planning), create necessary helper methods
        self.name = name
        self.description = description
        self.agent_pool = agent_pool
        self.shared_memory = shared_memory
        self.belief = belief
        self.action_selector = action_selector
        self.num_runs = num_runs

        self.planning = TaskPlanning(llm)

    def plan(self, task: str):
        """
        Plan the next action for the agent pool
        """
        # TODO: save task and agent pool description to shared memory

        self.shared_memory.add(
            event_type=EventType.planning, agent=self.name, content=task
        )
        agent_pool_description = self.agent_pool.get_agent_pool_description()

        # TODO: why do we need to add this? This seems to be a belief or observation
        self.shared_memory.add(
            event_type=EventType.planning,
            agent="Agent pool description",
            content=agent_pool_description,
        )

        # run the planning
        plan = self.planning.execute(task, agent_pool_description)

        print(str(plan))

        for step in plan.steps:
            self.shared_memory.add(
                event_type=EventType.task, agent=step.agent_name, content=step.task
            )

        return plan
