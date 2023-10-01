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
    config = OrchestratorConfig(llm_name="gpt-4")

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
        num_steps=3,
    )

    critic_agent = Critic(llm=orchestrator.llm, ratio=9, shared_memory=shared_memeory)
    # plan = orchestrator.plan(objective, planner, critic_agent)

    plan_text = """Step 1:
Agent: Sahar
Task: Sahar will collect and analyze satellite imagery data relevant to tropical cyclones, identifying features and patterns correlating with cyclone intensity and wind speed. She will work with a Meteorologist (to be hired) for parameter accuracy and relevance. Sahar will also address data privacy and security issues during data collection and develop a detailed contingency plan for any potential challenges. The duration for this task is estimated to be 2 months with a budget allocation of $10,000.
Step 2:
Agent: Physicist
Task: The physicist, in collaboration with the Meteorologist, will develop a theoretical model that estimates tropical cyclone maximum wind speed using Sahar's parameters. They will ensure model robustness, validate it using simulations and historical cyclone data, and prepare a detailed validation plan. This step is expected to take 3 months and has a budget of $15,000.
Step 3:
Agent: ML Engineer
Task: The ML Engineer will implement the theoretical model using machine learning algorithms, training, testing, and validating it using satellite imagery data. They will prepare a comprehensive report on performance, reliability, and improvement areas, ensuring clear communication to stakeholders. Concurrently, Amir will conduct a peer review of the machine learning model to externally validate the findings and ensure their accuracy and reliability. Both agents will also address data security during the processing and analysis stages. This dual-task step is expected to last 3 months and has a budget allocation of $20,000.
"""
    plan = planner.planning.post_process(plan_text)
    shared_memeory.add(EventType.planning, "Planner", str(plan))

    assert len(plan.steps) > 0

    assert user_agent1.shared_memory == physicist.shared_memory

    orchestrator.execute(plan, planner)
