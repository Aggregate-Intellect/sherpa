from sherpa_ai.agents.agent_pool import AgentPool
from sherpa_ai.agents.base import BaseAgent


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
    ):
        # TODO: Define agent actions (planning), create necessary helper methods
        raise NotImplementedError

    def plan(self, task: str):
        """
        Plan the next action for the agent pool
        """
        # TODO: save task and agent pool description to shared memory

        # run the planning
        self.run()

        # TODO: return result
        raise NotImplementedError
