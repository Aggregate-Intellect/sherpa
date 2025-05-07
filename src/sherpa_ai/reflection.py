from os import environ
from typing import List

from langchain_core.language_models import BaseLanguageModel 
from langchain_core.messages import BaseMessage 
from langchain_core.tools import BaseTool 
from loguru import logger 

from sherpa_ai.prompt_generator import PromptGenerator


class Reflection:
    """Class for performing reflection on AI actions.

    This class provides functionality to evaluate and refine AI actions based on
    feedback and previous actions. It includes methods for creating message history,
    evaluating action outcomes, and updating the AI's response format.

    Attributes:
        llm (BaseLanguageModel): The language model to use for evaluation.
        tools (List[BaseTool]): The tools available to the AI.
        action_list (List): The list of previous actions.

    Example:
        >>> from langchain_core.language_models import BaseLanguageModel
        >>> from langchain_core.tools import BaseTool
        >>> from sherpa_ai.reflection import Reflection
        >>> llm = ChatOpenAI(model="gpt-4o-mini")
        >>> tools = [MyTool()]
        >>> reflection = Reflection(llm, tools)
        >>> reflection.evaluate_action("action", "reply", "task", "previous_message")
        "new_reply"
    """
    
    def __init__(
        self, llm: BaseLanguageModel, tools: List[BaseTool], action_list: List = []
    ):
        """Initialize the Reflection class.

        Args:
            llm (BaseLanguageModel): The language model to use for evaluation.
            tools (List[BaseTool]): The tools available to the AI.
            action_list (List, optional): The list of previous actions. Defaults to an empty list.

        Example:
            >>> from langchain_core.language_models import BaseLanguageModel
            >>> from langchain_core.tools import BaseTool
            >>> from sherpa_ai.reflection import Reflection
            >>> llm = ChatOpenAI(model="gpt-4o-mini")
            >>> tools = [MyTool()]
            >>> reflection = Reflection(llm, tools)
        """
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
        """Create a message history from a list of messages.

        This method takes a list of BaseMessage objects and returns a string
        representing the message history. It reverses the order of the messages
        and stops adding tokens when the maximum token limit is reached.

        Args:
            messages (List[BaseMessage]): The list of messages to create a history from.
            max_token (int, optional): The maximum number of tokens to include in the history. Defaults to 2000.

        Returns:
            str: The message history as a string.

        Example:
            >>> from langchain_core.messages import HumanMessage, AIMessage
            >>> messages = [HumanMessage(content="Hello"), AIMessage(content="Hi")]
            >>> reflection = Reflection(llm, [])
            >>> message_history = reflection.create_message_history(messages)
            >>> print(message_history)
        """
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
        """Evaluate the action taken by the AI.

        This method evaluates the action taken by the AI based on the feedback
        and previous actions. It updates the AI's response format if necessary.

        Args:
            action (str): The action taken by the AI.
            assistant_reply (str): The reply from the AI.
            task (str): The task to solve.
            previous_message (List[BaseMessage]): The previous messages.

        Returns:
            str: The new reply from the AI.

        Example:
            >>> from langchain_core.messages import HumanMessage, AIMessage
            >>> messages = [HumanMessage(content="Hello"), AIMessage(content="Hi")]
            >>> reflection = Reflection(llm, [])
            >>> new_reply = reflection.evaluate_action("action", "reply", "task", messages)
            >>> print(new_reply)
        """
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
                return self.llm.invoke(instruction)
            else:
                return assistant_reply
