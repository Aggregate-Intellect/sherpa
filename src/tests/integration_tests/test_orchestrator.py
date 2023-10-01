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

logger.remove()
logger.add(sys.stderr, level="DEBUG")


user_description1 = """Sahar is skilled in astronomy and astrophysics. She has a PhD in those areas specializing in star formation.
Her expertise lies in developing and implementing models to study the formation mechanisms for galaxies and stars and applying computer vision algorithms to galaxy spectrum data.
She can answer questions about general astrophysics topics and also in depth technical details of modelling and galaxy and star formation questions and numerical methods related to these areas.
"""

user_description2 = """Amir is skilled in quantum physics, quantum information, quantum computing, quantum optics, quantum simulations, and atomic physics. He has a PhD in those areas specializing in experimental implementation of quantum computing gates.
His expertise lies in developing models to study the behavior of quantum optical systems, and building experimental setups to test out various hypothesis using data driven techniques.
He can answer questions about general quantum mechanics topics and also in depth technical details of modelling and implementing quantum optics experiments.
"""


def test_planning():
    objective = "Write a proposal for estimating the maximum wind speed of a tropical cyclone using satellite imagery"
    config = OrchestratorConfig(llm_name='gpt-4')

    orchestrator = Orchestrator(config=config)

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
    # plan = orchestrator.plan(objective, planner, critic_agent)
    # print(plan)

    plan_text = """Step 1:
Agent: ML Engineer
Task: Research and identify machine learning algorithms suitable for analyzing satellite imagery data to estimate wind speed of tropical cyclones. Specifically, focus on algorithms that have been successfully used for similar tasks in the past and have proven accuracy and reliability.
Step 2:
Agent: Physicist
Task: Collaborate with the physicist to understand the underlying physics principles and equations that govern the relationship between satellite imagery features and wind speed of tropical cyclones. Gather insights and guidance on how to incorporate physics-based models into the analysis. Discuss the potential benefits of integrating physics-based models with machine learning algorithms for more accurate estimation.
Step 3:
Agent: Sahar
Task: Consult with Sahar to understand the specific requirements and challenges related to using satellite imagery for estimating wind speed of tropical cyclones. Seek her expertise in computer vision algorithms and numerical methods for analyzing the satellite data. Discuss potential approaches and techniques that can be applied to enhance the accuracy of wind speed estimation.
Step 4:
Agent: ML Engineer
Task: Work with the ML Engineer to develop and train a machine learning model using the identified algorithms and the satellite imagery data. Collaborate on optimizing the model's performance and accuracy in estimating the maximum wind speed of tropical cyclones. Ensure that the chosen algorithms are appropriate for the task and can provide accurate results.
Step 5:
Agent: Sahar
Task: Consult with Sahar to explore the possibility of using computer vision algorithms and advanced image processing techniques to extract relevant features from the satellite imagery data. Collaborate on implementing these techniques to enhance the accuracy of wind speed estimation."""
    plan = planner.planning.post_process(plan_text)
    shared_memeory.add(EventType.planning, "Planner", str(plan))

    assert len(plan.steps) > 0

    assert user_agent1.shared_memory == physicist.shared_memory

    orchestrator.execute(plan, planner)
