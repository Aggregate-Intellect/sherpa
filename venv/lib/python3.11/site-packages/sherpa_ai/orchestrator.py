from typing import List, Optional

from langchain_openai import ChatOpenAI 
from pydantic import BaseModel 

from sherpa_ai.actions.planning import Plan
from sherpa_ai.agents import AgentPool, Critic, MLEngineer, Physicist, Planner
from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.events import EventType
from sherpa_ai.memory import Belief, SharedMemory


class OrchestratorConfig(BaseModel):
    llm_name: str = "gpt-3.5-turbo"
    llm_temperature: float = 0.7
    critic_rounds: int = 3


class Orchestrator:
    def __init__(self, config: OrchestratorConfig, agent_pool: AgentPool = AgentPool()):
        self.config = config

        self.agent_types = [MLEngineer, Physicist]
        self.llm = ChatOpenAI(
            model_name=self.config.llm_name, temperature=self.config.llm_temperature
        )
        self.agent_pool = agent_pool
        self.shared_memory = SharedMemory(
            objective="", agent_pool=self.agent_pool)

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

    def execute(self, plan: Plan, planner: Planner):
        agent_pool = self.agent_pool
        shared_memory = self.shared_memory

        for step in plan.steps:
            # log the task to the shared memory for the agent to execute
            agent = agent_pool.get_agent(step.agent_name)

            shared_memory.current_step = step
            shared_memory.add(EventType.task, planner.name, step.task)

            agent.run()

    def add_agent(self, agent: BaseAgent):
        self.agent_pool.add_agent(agent)

    def run(self, task):
        # initialize agents and shared_memories
        agent_pool = self.agent_pool
        shared_memory = self.shared_memory
        shared_memory.objective = task

        # initialize the planner and critic
        planner = Planner(
            name="planner",
            agent_pool=agent_pool,
            shared_memory=shared_memory,
            llm=self.llm,
        )
        critic = Critic(shared_memory=shared_memory)

        plan = self.plan(task, planner, critic)
        shared_memory.plan = plan

        for step in plan.steps:
            # log the task to the shared memory for the agent to execute
            agent = agent_pool.get_agent(step.agent_name)

            shared_memory.current_step = step
            shared_memory.add(EventType.task, planner.name, step.task)

            agent.run()

    def save(self, shared_memory: SharedMemory, agents: List[BaseAgent]):
        # save the shared memory and agents
        result = {}
        result["shared_memory"] = shared_memory.__dict__
        result["agent_belief"] = {
            agent.name: agent.belief.__dict__ for agent in agents}

        return result

    @classmethod
    def restore(cls, data: dict, agent_pool: AgentPool):
        # restore the shared memory and agents
        shared_memory = SharedMemory.from_dict(
            data["shared_memory"], agent_pool)
        agent_belief = data["agent_belief"]
        for name, agent in agent_pool.agents.items():
            agent.belief = Belief.from_dict(agent_belief[name])

        orchestrator = cls(OrchestratorConfig())
        orchestrator.shared_memory = shared_memory
        orchestrator.agent_pool = agent_pool
        return orchestrator

    def continue_with_user_feedback(self, user_feedback) -> Optional[str]:
        current_step = self.shared_memory.current_step

        current_step_id = self.shared_memory.events.index(current_step)
        agent_pool = self.agent_pool
        shared_memory = self.shared_memory

        self.shared_memory.add(
            EventType.result, current_step.agent_name, user_feedback)

        # continue with the next step
        for i in range(current_step_id + 1, len(self.shared_memory.plan.steps)):
            step = self.shared_memory.plan.steps[i]
            agent = agent_pool.get_agent(step.agent_name)
            shared_memory.current_step = step
            shared_memory.add(EventType.task, agent.name, step.task)

            agent.run()
