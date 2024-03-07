from argparse import ArgumentParser

from langchain.schema import HumanMessage
from slackapp.utils import get_qa_agent_from_config_file

import sherpa_ai.config as cfg
from sherpa_ai.events import EventType

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--config", type=str)
    args = parser.parse_args()

    qa_agent = get_qa_agent_from_config_file(args.config)
    

    while True:
        question = input("Ask me a question: ")
        qa_agent.shared_memory.add(EventType.task, "human", question)
        result = qa_agent.run()
        print(result)