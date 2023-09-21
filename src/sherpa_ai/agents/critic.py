from sherpa_ai.agents.agent_pool import AgentPool
from sherpa_ai.agents.base import BaseAgent


class Critic(BaseAgent):
    """
    The critic agent receives a plan from the planner and evaluate the plan based on
    some pre-defined metrics. At the same time, it gives the feedback to the planner.
    """

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
        # TODO: Define agent actions (critic), create necessary helper methods
        raise NotImplementedError
