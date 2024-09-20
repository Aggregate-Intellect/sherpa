from argparse import ArgumentParser

from hydra.utils import instantiate
from loguru import logger
from omegaconf import OmegaConf
from states import add_qa_sm

from sherpa_ai.agents import QAAgent
from sherpa_ai.events import Event, EventType


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

    config = OmegaConf.load(config_path)

    agent_config = instantiate(config.agent_config)
    config = instantiate(config.config, agent_config=agent_config)

    for action in config["actions"].values():
        action.belief = config["agent"].belief

    actions = {
        "answer_question": config["actions"]["summarize"],
        "query_document": config["actions"]["doc_search"],
        "start_qa": config["actions"]["start_qa"],
        "is_finished": config["actions"]["doc_search"].is_finished,
    }

    return config["agent"], actions


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--config", type=str, default="agent_config.yml")
    args = parser.parse_args()

    qa_agent, actions = get_qa_agent_from_config_file(args.config)

    qa_agent.belief.set_current_task(
        Event(EventType.task, "user", "Perform tasks"))
    logger.warning(qa_agent.belief.current_task)
    add_qa_sm(qa_agent.belief, actions)

    qa_agent.run()
