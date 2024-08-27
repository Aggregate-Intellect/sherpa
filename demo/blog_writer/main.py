import json
import os

from argparse import ArgumentParser
from loguru import logger

from hydra.utils import instantiate
from omegaconf import OmegaConf
from outliner import Outliner
from sherpa_ai.agents import QAAgent, UserAgent
from sherpa_ai.events import EventType

#create Output folder
directory_name = "Output"
if not os.path.exists(directory_name):
    os.mkdir(directory_name)
    logger.debug(f"Directory '{directory_name}' created successfully.")
else:
    logger.debug(f"Directory '{directory_name}' already exists.")

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


def get_user_agent_from_config_file(
    config_path: str,
) -> UserAgent:
    """
    Create a UserAgent from a config file.

    Args:
        config_path: Path to the config file

    Returns:
        UserAgent: A UserAgent instance
    """

    config = OmegaConf.load(config_path)

    user: UserAgent = instantiate(config.user)

    return user


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--config", type=str, default="agent_config.yaml")
    parser.add_argument("--transcript", type=str, default="transcript.txt")
    parser.add_argument("--blueprint", type=str, help="Optional JSON blueprint file to use")
    args = parser.parse_args()

    base_name = os.path.splitext(os.path.basename(args.transcript))[0]
    json_output_path = f"Output/blueprint_{base_name}.json"
    md_output_path = f"Output/blog_{base_name}.md"
    
    if args.blueprint:
        blueprint_full_path = os.path.join("Output", args.blueprint)
        if os.path.isfile(blueprint_full_path):
            with open(blueprint_full_path, 'r') as file:
                pure_json_str = file.read()
        else:
            # Assume outliner creates a new blueprint if not found
            outliner = Outliner(args.transcript)
            blueprint = outliner.full_transcript2outline_json(verbose=True)
            if blueprint.startswith("```"):
                lines = blueprint.split("\n")[1:-1]
                pure_json_str = "\n".join(lines)
            else:
                pure_json_str = blueprint
            with open(json_output_path, "w", encoding="utf-8") as f:
                f.write(pure_json_str)
            logger.debug(f"Blueprint generated and saved to {json_output_path}")
    else:
        # If no blueprint file is specified, proceed with creating a new one
        outliner = Outliner(args.transcript)
        blueprint = outliner.full_transcript2outline_json(verbose=True)
        if blueprint.startswith("```"):
            lines = blueprint.split("\n")[1:-1]
            pure_json_str = "\n".join(lines)
        else:
            pure_json_str = blueprint
        with open(json_output_path, "w", encoding="utf-8") as f:
            f.write(pure_json_str)
        logger.debug(f"Blueprint generated and saved to {json_output_path}")
        
    writer_agent = get_qa_agent_from_config_file(args.config)
    reviewer_agent = get_user_agent_from_config_file(args.config)
    parsed_json = json.loads(pure_json_str)

    blog = ""
    thesis = parsed_json.get("Thesis Statement", "")
    blog += f"# Introduction\n{thesis}\n"
    arguments = parsed_json.get("Supporting Arguments", [])
    for argument in arguments:
        blog += f"## {argument['Argument']}\n"
        evidences = argument.get("Evidence", [])
        for evidence in evidences:
            writer_agent.shared_memory.add(EventType.task, "human", evidence)
            result = writer_agent.run()

            reviewer_input = (
                "\n"
                "Please review the paragraph generated below. "
                "Type 'yes', 'y' or simply press Enter if everything looks good. "
                "Else provide feedback on how you would like the paragraph changed."
                "\n\n" + result
            )
            reviewer_agent.shared_memory.add(EventType.task, "human", reviewer_input)

            decision = reviewer_agent.run()
            decision_event = reviewer_agent.shared_memory.get_by_type(EventType.result)
            decision_content = decision_event[-1].content

            if decision_content == []:
                break
            #
            if decision_content.lower() in ["yes", "y", ""]:
                pass
            else:
                writer_agent.shared_memory.add(EventType.task, "human", decision_content)
                result = writer_agent.run()

            blog += f"{result}\n"

    with open(md_output_path, "w", encoding="utf-8") as f:
        f.write(blog)

    logger.debug("\nBlog generated successfully!\n")
