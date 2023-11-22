import sys

from loguru import logger

import sherpa_ai.config
from sherpa_ai.agents import (
    AgentPool,
    Critic,
    MLEngineer,
    Physicist,
    Planner,
    UserAgent,
)
from sherpa_ai.events import EventType
from sherpa_ai.memory import SharedMemory
from sherpa_ai.orchestrator import Orchestrator, OrchestratorConfig
from tests.fixtures.llms import get_llm

logger.remove()
logger.add(sys.stderr, level="INFO")


user_description1 = """Sahar is skilled in astronomy and astrophysics. She has a PhD in those areas specializing in star formation.
Her expertise lies in developing and implementing models to study the formation mechanisms for galaxies and stars and applying computer vision algorithms to galaxy spectrum data.
She can answer questions about general astrophysics topics and also in depth technical details of modelling and galaxy and star formation questions and numerical methods related to these areas.
"""  # noqa E501

user_description2 = """Amir is skilled in quantum physics, quantum information, quantum computing, quantum optics, quantum simulations, and atomic physics. He has a PhD in those areas specializing in experimental implementation of quantum computing gates.
His expertise lies in developing models to study the behavior of quantum optical systems, and building experimental setups to test out various hypothesis using data driven techniques.
He can answer questions about general quantum mechanics topics and also in depth technical details of modelling and implementing quantum optics experiments.
"""  # noqa E501


def test_planning(get_llm):
    objective = "Write a proposal for estimating the maximum wind speed of a tropical cyclone using satellite imagery"  # noqa E501
    config = OrchestratorConfig()

    orchestrator = Orchestrator(config=config)

    llm = get_llm(__file__, test_planning.__name__)
    orchestrator.llm = llm

    shared_memeory = SharedMemory(
        objective=objective,
    )
    orchestrator.shared_memory = shared_memeory

    physicist = Physicist(llm=orchestrator.llm, shared_memory=shared_memeory)

    ml_engineer = MLEngineer(llm=orchestrator.llm, shared_memory=shared_memeory)

    agent_pool = AgentPool()
    agent_pool.add_agents([physicist, ml_engineer])

    orchestrator.agent_pool = agent_pool

    planner = Planner(
        agent_pool=agent_pool,
        shared_memory=shared_memeory,
        llm=orchestrator.llm,
        num_steps=5,
    )

    plan_text = """Step 1:
Agent: ML Engineer
Task: Research and identify machine learning algorithms suitable for analyzing satellite imagery data to estimate wind speed of tropical cyclones. Specifically, focus on algorithms that have been successfully used for similar tasks in the past and have proven accuracy and reliability.
Step 2:
Agent: Physicist
Task: Collaborate with the physicist to understand the underlying physics principles and equations that govern the relationship between satellite imagery features and wind speed of tropical cyclones. Gather insights and guidance on how to incorporate physics-based models into the analysis. Discuss the potential benefits of integrating physics-based models with machine learning algorithms for more accurate estimation.
Step 3:
Agent: ML Engineer
Task: Work with the ML Engineer to develop and train a machine learning model using the identified algorithms and the satellite imagery data. Collaborate on optimizing the model's performance and accuracy in estimating the maximum wind speed of tropical cyclones. Ensure that the chosen algorithms are appropriate for the task and can provide accurate results.
"""  # noqa E501

    plan = planner.planning.post_process(plan_text)
    shared_memeory.add(EventType.planning, "Planner", str(plan))

    assert len(plan.steps) > 0

    assert ml_engineer.shared_memory == physicist.shared_memory

    orchestrator.execute(plan, planner)

    results = shared_memeory.get_by_type(EventType.result)

    assert len(results) > 0
