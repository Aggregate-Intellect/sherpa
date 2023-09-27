from langchain.chat_models import ChatOpenAI
from pydantic import BaseModel

from sherpa_ai.actions.planning import Plan
from sherpa_ai.agents import (
    AgentPool,
    Critic,
    MLEngineer,
    Physicist,
    Planner,
    Programmer,
    UserAgent,
)
from sherpa_ai.memory import EventType, SharedMemory


class OrchestratorConfig(BaseModel):
    llm_name: str = "gpt-3.5-turbo"
    llm_temperature: float = 0.7
    critic_rounds: int = 3


class Orchestrator:
    def __init__(self, config: OrchestratorConfig):
        self.config = config

        self.agent_types = [MLEngineer, Physicist, Programmer, UserAgent]
        self.llm = ChatOpenAI(
            model_name=self.config.llm_name, temperature=self.config.llm_temperature
        )

    def plan(self, task: str, planner: Planner, critic: Critic) -> Plan:
        # planner critic loop
        for _ in range(self.config.critic_rounds):
            # planner
            plan = planner.plan(task)

            # critic
            feedback = critic.get_feedback(task, str(plan))
            if feedback == "":
                break

        return plan

    def run(self, task):
        # initialize agents and shared_memories
        agent_pool = AgentPool()
        shared_memory = SharedMemory(objective=task, agent_pool=agent_pool)

        # TODO: pass arguments for agent initialization
        agents = [agent(shared_memory=shared_memory) for agent in self.agent_types]
        agent_pool.add_agents(agents)

        # initialize the planner and critic
        planner = Planner(
            name="planner",
            agent_pool=agent_pool,
            shared_memory=shared_memory,
            llm=self.llm,
        )
        critic = Critic(shared_memory=shared_memory)

        plan = self.plan(task, planner, critic)

        for step in plan.steps:
            # log the task to the shared memory for the agent to execute
            agent = agent_pool.get_agent(step.agent_name)

            shared_memory.current_step = step
            shared_memory.add(EventType.task, planner.name, step.task)

            agent.run()

        # TODO: How can the result be passed back to the user?
