import openai
from os import environ
from langchain.chat_models import ChatOpenAI
from prompt_generator import PromptGenerator

class Reflection():
    def __init__(self, tools, action_list = []):
        self.action_list = action_list
        prompt = PromptGenerator()
        self.format = prompt.response_format
        self.commands = [
                f"{i + 1}. {prompt._generate_command_string(item)}"
                for i, item in enumerate(tools)
            ]
  
    # we will also include previous_messages in the sherpa system
    def evaluate_action(self, action, assistant_reply, task, previous_message):
        self.action_list.append(action)
        if len(self.action_list) == 1:  # first action, no previous action
            return assistant_reply
        else:
            previous_action = self.action_list[-2]
            if previous_action == action:   # duplicate action
                instruction = (
                    f"You want to solve the task: {task}."
                    f"The original reply is: {assistant_reply}"
                    f"Here is all the commands you can choose to use: {self.commands}"
                    f"Here is previous messages: {previous_message}"
                    f"We need a new reply by changing neither command.name or command.args.query."
                    f"Make sure the new reply is different from the original reply by name or query."
                    f"You should only respond in JSON format as described below without any extra text. Do not return the TaskAction object."
                    f"Format for the new reply: {self.format}"
                    f"Ensure the response can be parsed by Python json.loads"
                    f"New reply:\n\n"
                )
                openai.api_key = environ.get("OPENAI_API_KEY")
                response = openai.Completion.create(
                            engine="text-davinci-003",
                            prompt= instruction,
                            temperature=0.7,
                            max_tokens=1024,
                            top_p=1,
                            frequency_penalty=0,
                            presence_penalty=0
                        )
                return response['choices'][0]['text']
            else:
                return assistant_reply