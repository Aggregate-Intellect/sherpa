from unittest.mock import patch
from loguru import logger

from sherpa_ai.actions.google_search import GoogleSearch
from sherpa_ai.agents.user import UserAgent
from sherpa_ai.agents.qa_agent import QAAgent
from sherpa_ai.events import EventType
from sherpa_ai.memory import SharedMemory


from sherpa_ai.policies.agent_feedback_policy import AgentFeedbackPolicy
from sherpa_ai.test_utils.llms import get_llm


def test_feedback_policy_in_qa(
    get_llm,
):
    test_id = 0
    llm = get_llm(__file__, test_feedback_policy_in_qa.__name__ + f"_{str(test_id)}")
    question = "What is the biggest ?"
    shared_memory = SharedMemory(agent_pool=None, objective=" Answer the question")
    google_search = GoogleSearch(
        role_description="Act as a question answering agent",
        task=" Question answering",
        llm=llm,
    )

    agent = UserAgent("Agent", "An agent to help the user", shared_memory=shared_memory)

    policy = AgentFeedbackPolicy(
        agent=agent, llm=llm, role_description="", output_instruction=""
    )
    qa_agent = QAAgent(
        llm=llm,
        shared_memory=shared_memory,
        num_runs=3,
        actions=[google_search],
        belief=None,
        agent_config=None,
        policy=policy,
    )
    qa_agent.shared_memory.add(EventType.task, "human", question)
    result = qa_agent.run()
    assert True
