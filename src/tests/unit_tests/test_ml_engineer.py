from langchain.llms import OpenAI
from langchain.llms.base import LLM

import sherpa_ai.config as cfg
from sherpa_ai.agents.ml_engineer import MLEngineer

def test_search_arxiv():
    llm = OpenAI(openai_api_key=cfg.OPENAI_API_KEY, temperature=0)
    critic_agent = MLEngineer(name="MLEngineerAgent")
    search_result = critic_agent.search_arxiv(query="ml", top_k=5)
    assert len(search_result) is 5
    assert search_result[0] is not ""