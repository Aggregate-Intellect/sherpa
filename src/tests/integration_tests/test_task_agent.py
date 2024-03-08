from datetime import datetime
from typing import List

import pytest
from langchain.chat_models import ChatOpenAI
from langchain.llms import FakeListLLM
from langchain.tools.base import BaseTool
from langchain.vectorstores.base import VectorStoreRetriever

import sherpa_ai.config as cfg
from sherpa_ai.connectors.vectorstores import get_vectordb
from sherpa_ai.task_agent import TaskAgent
from sherpa_ai.test_utils.llms import get_llm
from sherpa_ai.tools import ContextTool, SearchTool


def config_task_agent(
    tools: List[BaseTool],
    memory: VectorStoreRetriever,
    llm=None,
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


@pytest.mark.external_api
def test_task_solving_with_search_succeeds(get_llm):  # noqa: F811
    """Test task solving with search"""
    question = "What is the date today, using the following format: YYYY-MM-DD?"

    memory = get_vectordb()
    tools = [SearchTool()]

    llm = get_llm(__file__, test_task_solving_with_search_succeeds.__name__)

    date = (
        llm.responses[-1]
        if isinstance(llm, FakeListLLM)
        else datetime.now().strftime("%Y-%m-%d")
    )

    task_agent = config_task_agent(tools=tools, memory=memory, llm=llm)

    response = task_agent.run(question)
    assert date in response, "Today's date not found in response"


@pytest.mark.external_api
def test_task_solving_with_context_search_succeeds(get_llm):  # noqa: F811
    question = "What is langchain?"

    if cfg.VECTORDB != "pinecone" and cfg.VECTORDB != "chroma":
        pytest.skip("VECTORDB is not configured properly, skipping this test")

    memory = get_vectordb()
    tools = [ContextTool(memory=memory)]

    llm = get_llm(__file__, test_task_solving_with_context_search_succeeds.__name__)
    task_agent = config_task_agent(tools=tools, memory=memory, llm=llm)

    response = task_agent.run(question)

    assert "langchain" in response.lower(), "langchain not found in response"
