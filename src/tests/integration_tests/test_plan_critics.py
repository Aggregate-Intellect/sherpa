import sys

import pytest
from loguru import logger

from sherpa_ai.agents import (AgentPool, Critic, MLEngineer, Physicist,
                              Planner, UserAgent)
from sherpa_ai.memory import SharedMemory
from sherpa_ai.orchestrator import Orchestrator, OrchestratorConfig
from sherpa_ai.test_utils.llms import get_llm

logger.remove()
logger.add(sys.stderr, level="DEBUG")


user_description1 = """Sahar is skilled in astronomy and astrophysics. She has a PhD in those areas specializing in star formation.
Her expertise lies in developing and implementing models to study the formation mechanisms for galaxies and stars and applying computer vision algorithms to galaxy spectrum data.
She can answer questions about general astrophysics topics and also in depth technical details of modelling and galaxy and star formation questions and numerical methods related to these areas.
"""  # noqa E501

user_description2 = """Amir is skilled in quantum physics, quantum information, quantum computing, quantum optics, quantum simulations, and atomic physics. He has a PhD in those areas specializing in experimental implementation of quantum computing gates.
His expertise lies in developing models to study the behavior of quantum optical systems, and building experimental setups to test out various hypothesis using data driven techniques.
He can answer questions about general quantum mechanics topics and also in depth technical details of modelling and implementing quantum optics experiments.
"""  # noqa E501


@pytest.mark.external_api
def test_planning_succeeds(get_llm):  # noqa: F811
    objective = "Write a proposal for estimating the maximum wind speed of a tropical cyclone using satellite imagery"  # noqa E501
    config = OrchestratorConfig()

    orchestrator = Orchestrator(config=config)

    llm = get_llm(__file__, test_planning_succeeds.__name__)
    orchestrator.llm = llm

    shared_memeory = SharedMemory(
        objective=objective,
    )
    orchestrator.shared_memory = shared_memeory

    physicist = Physicist(llm=orchestrator.llm, shared_memory=shared_memeory)

    ml_engineer = MLEngineer(llm=orchestrator.llm, shared_memory=shared_memeory)

    user_agent1 = UserAgent(
        name="Sahar",
        description=user_description1,
        shared_memory=shared_memeory,
    )
    user_agent2 = UserAgent(
        name="Amir", description=user_description2, shared_memory=shared_memeory
    )

    agent_pool = AgentPool()
    agent_pool.add_agents([physicist, ml_engineer, user_agent1, user_agent2])

    orchestrator.agent_pool = agent_pool

    planner = Planner(
        agent_pool=agent_pool,
        shared_memory=shared_memeory,
        llm=orchestrator.llm,
        num_steps=5,
    )

    critic_agent = Critic(llm=orchestrator.llm, ratio=9, shared_memory=shared_memeory)
    plan = orchestrator.plan(objective, planner, critic_agent)

    assert len(plan.steps) > 0
