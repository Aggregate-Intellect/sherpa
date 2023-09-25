from sherpa_ai.agents.critic import Critic
import sherpa_ai.config as cfg
from langchain.llms.base import LLM
from langchain.llms import OpenAI

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
"""

def test_evaluation_matrices():
    description = """
    You are a Critic agent that receive a plan from the planner to execuate a task from user.
    Your goal is to output the 10 most necessary feedback given the corrent plan to solve the task.
    """
    llm = OpenAI(openai_api_key=cfg.OPENAI_API_KEY,temperature=0)
    critic_agent = Critic(name="CriticAgent", llm=llm)

    i_score, i_evaluation = critic_agent.get_importance_evaluation(task, plan)
    assert type(i_score) is int
    assert type(i_evaluation) is str

    d_score, d_evaluation = critic_agent.get_detail_evaluation(task, plan)
    assert type(d_score) is int
    assert type(d_evaluation) is str

def test_get_feedback():
    llm = OpenAI(openai_api_key=cfg.OPENAI_API_KEY,temperature=0)
    critic_agent = Critic(name="CriticAgent", llm=llm)
    feedback_list = critic_agent.get_feedback(task, plan)
    assert(len(feedback_list)==10)
    # assert type(feedback) is str
    # assert type(feedback) is not ""


