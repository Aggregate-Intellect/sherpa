from langchain.llms import OpenAI

import sherpa_ai.config as cfg
from sherpa_ai.actions.context_search import ContextSearch

def test_context_search():
    
    role_description =  "The programmer receives requirements about a program and write it"
    
    task = """We need to render a highly complex 3D image on the solar system. We can use any publicly avaliable
    resources to achieve this task."""  # noqa: E501
    
    llm = OpenAI(openai_api_key=cfg.OPENAI_API_KEY, temperature=0)
    
    context_search = ContextSearch(role_description=role_description, task=task, llm=llm)
    
    result = context_search.execute(task)
    
    assert(len(result) > 0)
