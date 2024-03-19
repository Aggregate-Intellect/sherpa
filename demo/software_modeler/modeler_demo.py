from argparse import ArgumentParser

from langchain.schema import HumanMessage
from slackapp.utils import get_qa_agent_from_config_file

import sherpa_ai.config as cfg
from sherpa_ai.events import EventType

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--config", type=str)
    parser.add_argument(
        "--desc", type=str, help="Path to a text file containing the domain description"
    )
    args = parser.parse_args()

    qa_agent = get_qa_agent_from_config_file(args.config)

    print(f"Generating domain model for {args.desc}")

    with open(args.desc, "r") as f:
        domain_desc = f.read()

    qa_agent.shared_memory.add(
        EventType.task,
        "human",
        f"Generate domain model the following description:\n {domain_desc}",
    )
    result = qa_agent.run()
    print(result)
