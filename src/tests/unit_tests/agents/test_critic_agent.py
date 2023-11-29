from unittest.mock import MagicMock

from sherpa_ai.agents.critic import Critic
from tests.fixtures.llms import get_llm

task = "Write a hello world program"
plan = """
1. Choose a Programming Language:
Decide which programming language you want to use. "Hello, World!" programs can be written in virtually any programming language, from Python and Java to C++ and JavaScript.

2. Set Up Your Development Environment:
Install any necessary tools or development environments for your chosen programming language. This might include a text editor or integrated development environment (IDE).

3. Write the Code:
Open your chosen code editor or IDE.
Create a new project or file for your "Hello, World!" program.
Write the code to display the "Hello, World!" message on the screen. The code will vary depending on the programming language. Here are some examples:
"""  # noqa: E501


def test_evaluation_matrices_succeeds(get_llm):  # noqa: F811
    llm = get_llm(__file__, test_evaluation_matrices_succeeds.__name__)
    critic_agent = Critic(llm=llm, ratio=1)

    i_score, i_evaluation = critic_agent.get_importance_evaluation(task, plan)
    assert type(i_score) is int
    assert type(i_evaluation) is str

    d_score, d_evaluation = critic_agent.get_detail_evaluation(task, plan)
    assert type(d_score) is int
    assert type(d_evaluation) is str


def test_get_feedback_succeeds(get_llm):  # noqa: F811
    llm = get_llm(__file__, test_get_feedback_succeeds.__name__)
    # set ratio to 2 to force feedback
    critic_agent = Critic(llm=llm, ratio=2, shared_memory=MagicMock())
    feedback_list = critic_agent.get_feedback(task, plan)
    assert len(feedback_list) == 3
