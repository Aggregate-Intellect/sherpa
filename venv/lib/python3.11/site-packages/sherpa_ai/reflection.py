from os import environ
from typing import List

from langchain_core.language_models import BaseLanguageModel 
from langchain_core.messages import BaseMessage 
from langchain_core.tools import BaseTool 
from loguru import logger 

from sherpa_ai.prompt_generator import PromptGenerator


class Reflection:
    def __init__(
        self, llm: BaseLanguageModel, tools: List[BaseTool], action_list: List = []
    ):
        self.llm = llm
        self.action_list = action_list

        self.token_counter = self.llm.get_num_tokens
        prompt = PromptGenerator()
        self.format = prompt.response_format
        self.commands = [
            f"{i + 1}. {prompt._generate_command_string(item)}"
            for i, item in enumerate(tools)
        ]

    def create_message_history(
        self, messages: List[BaseMessage], max_token=2000
    ) -> str:
        result = ""
        current_tokens = 0

        for message in reversed(messages):
            current_tokens = current_tokens + \
                self.token_counter(message.content)
            if current_tokens > max_token:
                break
            result = message.type + ": " + message.content + "\n" + result

        return result

    # we will also include previous_messages in the sherpa system
    def evaluate_action(self, action, assistant_reply, task, previous_message):
        self.action_list.append(action)
        if len(self.action_list) == 1:  # first action, no previous action
            return assistant_reply
        else:
            previous_action = self.action_list[-2]
            message_history = self.create_message_history(previous_message)
            if previous_action == action:  # duplicate action
                instruction = (
                    f"You want to solve the task: {task}."
                    f"The original reply is: {assistant_reply}"
                    f"Here is all the commands you can choose to use:"
                    f" {self.commands}"
                    f"Here is previous messages: \n{message_history}\n"
                    f"We need a new reply by changing neither command.name or command.args.query."
                    f"Make sure the new reply is different from the original reply by name or query."
                    f"You should only respond in JSON format as described below without any extra text. Do not return the TaskAction object."
                    f"Format for the new reply: {self.format}"
                    f"Ensure the response can be parsed by Python json.loads"
                    f"New reply:\n\n"
                )
                return self.llm.predict(instruction)
            else:
                return assistant_reply
