from datetime import datetime
from typing import List

import pytest
from langchain import GoogleSerperAPIWrapper
from langchain.chat_models import ChatOpenAI
from langchain.tools.base import BaseTool
from langchain.vectorstores.base import VectorStoreRetriever

import sherpa_ai.config as cfg
from sherpa_ai.connectors.vectorstores import get_vectordb
from sherpa_ai.task_agent import TaskAgent
from sherpa_ai.tools import ContextTool, SearchTool


def config_task_agent(
    tools: List[BaseTool],
    memory: VectorStoreRetriever,
    llm=ChatOpenAI(model_name="gpt-3.5-turbo"),
) -> TaskAgent:
    task_agent = TaskAgent.from_llm_and_tools(
        ai_name="Sherpa",
        ai_role="assistant",
        ai_id="Sherpa",
        memory=memory,
        tools=tools,
        previous_messages=[],
        llm=llm,
    )

    return task_agent


@pytest.mark.real
def test_task_solving_with_search():
    """Test task solving with search"""
    question = "What is the date today, using the following format: YYYY-MM-DD?"
    date = datetime.now().strftime("%Y-%m-%d")

    if cfg.SERPER_API_KEY is None:
        pytest.skip(
            "SERPER_API_KEY not found in environment variables, skipping this test"
        )
    memory = get_vectordb()
    tools = [SearchTool(api_wrapper=GoogleSerperAPIWrapper())]

    task_agent = config_task_agent(tools=tools, memory=memory)

    response = task_agent.run(question)
    assert date in response, "Today's date not found in response"


@pytest.mark.real
def test_task_solving_with_context_search():
    question = "What is langchain?"

    if cfg.VECTORDB != "pinecone" or cfg.VECTORDB != "chroma":
        pytest.skip("VECTORDB is not configured properly, skipping this test")

    memory = get_vectordb()
    tools = [ContextTool(memory=memory)]

    task_agent = config_task_agent(tools=tools, memory=memory)

    response = task_agent.run(question)

    assert "langchain" in response.lower(), "langchain not found in response"
