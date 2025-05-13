import time
from typing import Any, Callable, List

from langchain_core.messages import ( 
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.prompts import BaseChatPromptTemplate 
from langchain_core.vectorstores import VectorStoreRetriever 
from loguru import logger 
from pydantic import BaseModel 

from sherpa_ai.prompt_generator import get_prompt
from sherpa_ai.tools import BaseTool


class SlackBotPrompt(BaseChatPromptTemplate):
    """A chat prompt template for a Slack bot.

    This class extends BaseChatPromptTemplate to provide a specialized prompt template
    for Slack bots. It handles message formatting, token counting, and chat history
    processing.

    Attributes:
        ai_name (str): The name of the AI assistant.
        ai_role (str): The role of the AI assistant.
        tools (List[BaseTool]): List of tools available to the AI.
        token_counter (Callable[[str], int]): Function to count tokens in a string.
        send_token_limit (int): Maximum number of tokens to send in a message.
            Defaults to 4196.

    Example:
        >>> from sherpa_ai.prompt import SlackBotPrompt
        >>> prompt = SlackBotPrompt(
        ...     ai_name="Assistant",
        ...     ai_role="Helper",
        ...     tools=[],
        ...     token_counter=lambda x: len(x.split())
        ... )
        >>> messages = prompt.format_messages(task="Hello", user_input="Hi")
        >>> print(len(messages))
        3
    """
    ai_name: str
    ai_role: str
    tools: List[BaseTool]
    token_counter: Callable[[str], int]
    send_token_limit: int = 4196

    def construct_base_prompt(self):
        """Construct the base prompt for the AI assistant.

        This method generates the foundational system prompt that defines the AI's
        identity, role, and available tools. It combines the AI's name with the
        prompt generated from available tools.

        Returns:
            str: The complete base prompt string.

        Example:
            >>> from sherpa_ai.prompt import SlackBotPrompt
            >>> prompt = SlackBotPrompt(
            ...     ai_name="Assistant",
            ...     ai_role="Helper",
            ...     tools=[],
            ...     token_counter=lambda x: len(x.split())
            ... )
            >>> base = prompt.construct_base_prompt()
            >>> print(base.startswith("You are"))
            True
        """
        full_prompt = f"You are a friendly assistent bot called"
        f" {self.ai_name}\n\n"
        full_prompt += f"\n\n{get_prompt(self.tools)}"
        logger.debug(full_prompt)
        return full_prompt

    def format_messages(self, **kwargs: Any) -> List[BaseMessage]:
        """Format messages for the bot, including system prompts and chat history.

        This method constructs a list of messages including:
        - Base system prompt defining the bot's identity
        - Current time and date
        - Recent chat history (up to token limit)
        - Current task and user input

        Args:
            **kwargs: Keyword arguments containing:
                - task (str): The current task description
                - messages (List[dict]): Previous chat messages
                - user_input (str): The user's input message

        Returns:
            List[BaseMessage]: List of formatted messages ready for the model.

        Example:
            >>> prompt = SlackBotPrompt(
            ...     ai_name="Assistant",
            ...     ai_role="Helper",
            ...     tools=[],
            ...     token_counter=lambda x: len(x.split())
            ... )
            >>> messages = prompt.format_messages(
            ...     task="Help user",
            ...     messages=[],
            ...     user_input="Hello"
            ... )
            >>> print(len(messages))
            3
        """
        base_prompt = SystemMessage(content=self.construct_base_prompt())
        time_prompt = SystemMessage(
            content=f"The current time and date is {time.strftime('%c')}"
        )
        used_tokens = self.token_counter(base_prompt.content) + self.token_counter(
            time_prompt.content
        )

        query = kwargs["task"]
        previous_messages = kwargs["messages"]

        input_message = f'Current task: {query} \n {kwargs["user_input"]}'

        historical_messages: List[BaseMessage] = []
        for message in previous_messages[-10:][::-1]:
            message_tokens = self.token_counter(message.content)
            if used_tokens + message_tokens > self.send_token_limit - 1000:
                break
            historical_messages = [message] + historical_messages
            used_tokens += message_tokens

        logger.debug(input_message)
        input_message = HumanMessage(content=input_message)

        messages: List[BaseMessage] = [base_prompt, time_prompt]
        messages += historical_messages
        messages.append(input_message)
        logger.debug(f"Base prompt: {base_prompt}")
        logger.debug(f"Time prompt: {time_prompt}")
        logger.debug(f"Historical messages: {historical_messages}")
        return messages

    def process_chat_history(self, messages: List[dict]) -> List[BaseMessage]:
        """Process raw chat history into formatted message objects.

        This method converts raw chat messages into appropriate message objects
        (AIMessage or HumanMessage) and handles message formatting.

        Args:
            messages (List[dict]): List of raw chat messages, each containing:
                - type (str): Message type ("message" or "text")
                - user (str): User identifier
                - text (str): Message content

        Returns:
            List[BaseMessage]: List of processed message objects.

        Example:
            >>> prompt = SlackBotPrompt(
            ...     ai_name="Assistant",
            ...     ai_role="Helper",
            ...     tools=[],
            ...     token_counter=lambda x: len(x.split())
            ... )
            >>> raw_messages = [
            ...     {"type": "message", "user": "user1", "text": "Hello"},
            ...     {"type": "message", "user": "assistant", "text": "Hi"}
            ... ]
            >>> processed = prompt.process_chat_history(raw_messages)
            >>> print(len(processed))
            2
        """
        results = []

        for message in messages:
            logger.debug(message)
            if message["type"] != "message" and message["type"] != "text":
                continue

            message_cls = AIMessage if message["user"] == self.ai_id else HumanMessage
            # replace the at in the message with the name of the bot
            text = message["text"].replace(
                f"@{self.ai_id}", f"@{self.ai_name}")
            results.append(message_cls(content=text))

        return results
