from sherpa_ai.agents.agent_pool import AgentPool
from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.actions.planning import TaskPlanning
from langchain.llms.base import LLM

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
        llm = LLM,
    ):
        # TODO: Define agent actions (planning), create necessary helper methods
        self.name = name
        self.description = description
        self.agent_pool = AgentPool
        self.shared_memory = shared_memory
        self.belief = belief
        self.action_selector = action_selector
        self.num_runs = num_runs
        
        self.planning = TaskPlanning(llm)
        
        # raise NotImplementedError

    def plan(self, task: str):
        """
        Plan the next action for the agent pool
        """
        # TODO: save task and agent pool description to shared memory
        
        # TODO: how is shared memory accessed?

        agent_pool_description = self.agent_pool.get_agent_pool_description()
        
        # run the planning
        plan = self.planning.execute(task, agent_pool_description)
        
        return plan
        # TODO: return result
        raise NotImplementedError
