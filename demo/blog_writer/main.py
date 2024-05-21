import json
from argparse import ArgumentParser

from hydra.utils import instantiate
from omegaconf import OmegaConf
from sherpa_ai.agents import QAAgent
from sherpa_ai.agents import UserAgent
from sherpa_ai.events import EventType

from outliner import Outliner

# from sherpa_ai.memory import Belief


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

    agent_config = instantiate(config.agent_config)
    user: UserAgent = instantiate(config.user)

    return user



if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--config", type=str, default="agent_config.yaml")
    parser.add_argument("--transcript", type=str, default="transcript.txt")
    args = parser.parse_args()

    writer_agent = get_qa_agent_from_config_file(args.config)
    reviewer_agent = get_user_agent_from_config_file(args.config)

    outliner = Outliner(args.transcript)
    blueprint = outliner.full_transcript2outline_json(verbose=True)
    if blueprint.startswith("```"):
        # The first and last lines are code block delimiters; remove them
        lines = blueprint.split("\n")[1:-1]
        pure_json_str = "\n".join(lines)
    else:
        pure_json_str = blueprint

    with open("blueprint.json", "w") as f:
        f.write(pure_json_str)

    #with open("blueprint.json", "r") as f:
    #    pure_json_str = f.read()

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


            reviewer_input= "\n" + "Please review the above para generated. Type yes, y and enter if everything looks good. Else tell us what do want to edit." + "\n" + result
            reviewer_agent.shared_memory.add(EventType.task, "human", reviewer_input)
            
            decision = reviewer_agent.run()
            decision_event= reviewer_agent.shared_memory.get_by_type(EventType.result)
            decision_content=decision_event[-1].content

            if decision_content == []:
                break
            #
            if decision_content.lower() in ["yes", "y", ""]:
                pass
            else:
                writer_agent.shared_memory.add(EventType.task, "human", decision_content)
                result = writer_agent.run()
            # writer_agent.belief = Belief()
            blog += f"{result}\n"

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
