import chainlit as cl
from argparse import ArgumentParser

from hydra.utils import instantiate
from loguru import logger
from omegaconf import OmegaConf
from states import add_qa_sm
import chainlit as cl
from sherpa_ai.agents import QAAgent
from sherpa_ai.events import Event, EventType


@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Morning routine ideation",
            message="Can you help me create a personalized morning routine that would help increase my productivity throughout the day? Start by asking me about my current habits and what activities energize me in the morning.",
            icon="/public/idea.svg",
        ),

        cl.Starter(
            label="Explain superconductors",
            message="Explain superconductors like I'm five years old.",
            icon="/public/learn.svg",
        ),
        cl.Starter(
            label="Python script for daily email reports",
            message="Write a script to automate sending daily email reports in Python, and walk me through how I would set it up.",
            icon="/public/terminal.svg",
        ),
        cl.Starter(
            label="Text inviting friend to wedding",
            message="Write a text asking a friend to be my plus-one at a wedding next month. I want to keep it super short and casual, and offer an out.",
            icon="/public/write.svg",
        )
    ]
def get_qa_agent_from_config_file(
    config_path: str,
) -> QAAgent:
    """
    Create a QAAgent from a config file.

    Args:
        config_path: Path to the config file

    Returns:
        QAAgent: A QAAgent instance
    """
    print("here in get qa")

    config = OmegaConf.load(config_path)
    print(config)
    agent_config = instantiate(config.agent_config)
    config = instantiate(config.config, agent_config=agent_config)
    print("2nd here in get qa")

    print(config)
    for action in config["actions"].values():
        action.belief = config["agent"].belief
    print("______________________________________________")
    print(config )
    actions = {
        "answer_question": config["actions"]["summarize"],
        "query_document": config["actions"]["doc_search"],
        "start_qa": config["actions"]["start_qa"],
        "is_finished": config["actions"]["doc_search"].is_finished,
    }

    return config["agent"], actions


@cl.on_message
async def main(message: cl.Message):
    # Example function to run your QA agent in a chat loop
    print("actions first")
    qa_agent, actions = get_qa_agent_from_config_file("agent_config.yml")
    print('actions')

    # Start the conversation
    await message.send("Welcome! You can ask your questions now. \n Ask your Question: ")

    while True:

        # Trigger your agent to handle the user question
        qa_agent.belief.set_current_task(
            Event(EventType.task, "user", message))
        add_qa_sm(qa_agent.belief, actions)
        result = qa_agent.run()

        await message.send(f"Here is your answer: {result}")
