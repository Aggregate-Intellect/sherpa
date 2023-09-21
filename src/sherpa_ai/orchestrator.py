from pydantic import BaseModel

from sherpa_ai.agents import (
    AgentPool,
    Critic,
    MLEngineer,
    Physicist,
    Planner,
    Programmer,
    UserAgent,
)
from sherpa_ai.memory import SharedMemory
from sherpa_ai.memory.events import event_types


class OrchestratorConfig(BaseModel):
    llm_name: str = "gpt-3.5-turbo"
    critic_rounds: int = 3


class Orchestrator:
    def __init__(self, config: OrchestratorConfig):
        self.config = config

        self.agent_types = [MLEngineer, Physicist, Programmer, UserAgent]

    def run(self, task):
        # initialize agents and shared_memories
        agent_pool = AgentPool()
        shared_memory = SharedMemory(objective=task, agent_pool=agent_pool)

        # TODO: pass arguments for agent initialization
        agents = [agent(shared_memory=shared_memory) for agent in self.agent_types]
        agent_pool.add_agents(agents)

        # initialize the planner and critic
        planner = Planner(shared_memory=shared_memory)
        critic = Critic(shared_memory=shared_memory)

        # planner critic loop
        for _ in range(self.config.critic_rounds):
            # planner
            plan = planner.plan()

            # critic
            approval = critic.criticize()
            if approval:
                break

        for step in plan.steps:
            # log the task to the shared memory for the agent to execute
            task_event_type = event_types["task"]
            agent = agent_pool.get_agent(step.agent_name)

            shared_memory.current_step = step
            shared_memory.add(task_event_type, planner.name, step.task)

            agent.run()

        # TODO: How can the result be passed back to the user?
