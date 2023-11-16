from langchain.llms import OpenAI

import sherpa_ai.config as cfg
from sherpa_ai.agents.agent_pool import AgentPool
from sherpa_ai.agents.physicist import Physicist
from sherpa_ai.agents.planner import Planner

# from sherpa_ai.agents.programmer import Programmer
from sherpa_ai.memory.shared_memory import SharedMemory


def test_planner():
    # programmer_description = (
    #     "The programmer receives requirements about a program and write it"
    # )
    # programmer = Programmer(name="Programmer", description=programmer_description)

    llm = OpenAI(openai_api_key=cfg.OPENAI_API_KEY, temperature=0)

    physicist_description = (
        "The physicist agent answers questions or research about physics-related topics"
    )
    physicist = Physicist(
        name="Physicist",
        description=physicist_description,
        llm=llm,
    )

    agent_pool = AgentPool()
    agent_pool.add_agents([physicist])

    shared_memory = SharedMemory(
        objective="Share the information across different agents.",
        agent_pool=agent_pool,
    )

    planner = Planner(
        name="planner",
        agent_pool=agent_pool,
        shared_memory=shared_memory,
        llm=llm,
    )

    task = """We need to render a highly complex 3D image on the solar system. We can use any publicly avaliable
    resources to achieve this task."""  # noqa: E501

    # shared_memory=None,
    # belief=None,
    # action_selector=None,
    # num_runs=1,

    p = planner.plan(task=task)
    assert len(p.steps) > 0
