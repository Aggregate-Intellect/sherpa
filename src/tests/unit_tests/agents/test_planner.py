from sherpa_ai.agents.agent_pool import AgentPool
from sherpa_ai.agents.physicist import Physicist
from sherpa_ai.agents.planner import Planner

# from sherpa_ai.agents.programmer import Programmer
from sherpa_ai.memory.shared_memory import SharedMemory
from sherpa_ai.test_utils.llms import get_llm


def test_planner_succeeds(get_llm):  # noqa: F811
    llm = get_llm(__file__, test_planner_succeeds.__name__)

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

    p = planner.plan(task=task)
    assert len(p.steps) > 0
