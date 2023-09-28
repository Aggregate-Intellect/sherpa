import sys

from loguru import logger

import sherpa_ai.config
from sherpa_ai.agents import AgentPool, Critic, Physicist, Planner, UserAgent
from sherpa_ai.memory import SharedMemory
from sherpa_ai.orchestrator import Orchestrator, OrchestratorConfig

logger.remove()
logger.add(sys.stderr, level="DEBUG")


def test_planning():
    objective = "Create a summary for application of quantum physics in astronomy"

    physicist_description = (
        "The physicist agent answers questions or research about physics-related topics"
    )
    physicist = Physicist(name="Physicist", description=physicist_description)

    user_agent1 = UserAgent(
        name="Amir",
        description="Amir is an expert in quantum computing and quantum physics",
    )
    user_agent2 = UserAgent(name="Kepler", description="Kepler is an expert in astronomy")

    config = OrchestratorConfig()
    orchestrator = Orchestrator(config=config)
    agent_pool = AgentPool()
    agent_pool.add_agents([physicist, user_agent1, user_agent2])

    shared_memeory = SharedMemory(
        objective="Share the information across different agents.",
        agent_pool=agent_pool,
    )

    planner = Planner(
        agent_pool=agent_pool,
        shared_memory=shared_memeory,
        llm=orchestrator.llm,
        num_steps=6
    )

    critic_agent = Critic(llm=orchestrator.llm, ratio=9, shared_memory=shared_memeory)

    plan = orchestrator.plan(objective, planner, critic_agent)

    assert len(plan.steps) > 0
