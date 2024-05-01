import json
from argparse import ArgumentParser

from hydra.utils import instantiate
from omegaconf import OmegaConf
from sherpa_ai.agents import QAAgent
from sherpa_ai.events import EventType

from outliner import Outliner


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
    qa_agent: QAAgent = instantiate(config.qa_agent, agent_config=agent_config)

    return qa_agent


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--config", type=str, default="agent_config.yaml")
    parser.add_argument("--transcript", type=str, default="transcript.txt")
    args = parser.parse_args()

    qa_agent = get_qa_agent_from_config_file(args.config)

    outliner = Outliner(args.transcript)
    blueprint = outliner.full_transcript2blueprint()
    if blueprint.startswith("```"):
        # The first and last lines are code block delimiters; remove them
        lines = blueprint.split("\n")[1:-1]
        pure_json_str = "\n".join(lines)
    else:
        pure_json_str = blueprint

    with open("blueprint.json", "w") as f:
        f.write(pure_json_str)

    parsed_json = json.loads(pure_json_str)

    blog = ""
    for key in parsed_json:
        blog += "# " + key + "\n"
        for question in parsed_json[key]:
            # Add the question to the shared memory. By default, the agent will take the last
            # message in the shared memory as the task.
            qa_agent.shared_memory.add(EventType.task, "human", question)
            result = qa_agent.run()
            blog += result + "\n"
        blog += "\n"

    with open("blog.md", "w") as f:
        f.write(blog)

    print("\nBlog generated successfully!\n")

    # save_format = None
    # while save_format is None:
    #     save_format = input(
    #         "Select format to save the blog in: 1. Markdown (Default) 2. ReStructured Text\n"
    #     )

    # if save_format == "2":
    #     output = pypandoc.convert("blog.md", "rst")
    #     if os.path.exists("blog.md"):
    #         os.remove("blog.md")
