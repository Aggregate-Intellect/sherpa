from sherpa_ai.actions.planning import TaskPlanning
import sherpa_ai.config as cfg
from langchain.llms.base import LLM
from langchain.llms import OpenAI


def test_planning():
    llm = OpenAI(openai_api_key=cfg.OPENAI_API_KEY,temperature=0)

    task_planning = TaskPlanning(llm)

    task = """We need to render a highly complex 3D image on the solar system. We can use any publicly avaliable
    resources to achieve this task."""

    agent_pool_description = """Agent: physicist
    Info: the physicist can answer question on any physics questions. 

    Agent: programmer
    Info: the programmer can write scripts to automate some tasks.
    """

    plan = task_planning.execute(task, agent_pool_description)

    print(str(plan))
    
    assert(len(plan.steps)>0)