import logging
import time
from typing import Any, Callable, List

from langchain.prompts.chat import BaseChatPromptTemplate
from langchain.schema import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain.vectorstores.base import VectorStoreRetriever
from pydantic import BaseModel

from prompt_generator import get_prompt
from tools import BaseTool

logger = logging.getLogger(__name__)


class SlackBotPrompt(BaseChatPromptTemplate, BaseModel):
    ai_name: str
    ai_role: str
    tools: List[BaseTool]
    token_counter: Callable[[str], int]
    send_token_limit: int = 4196

    def construct_base_prompt(self):
        full_prompt = f"You are a friendly assistent bot called {self.ai_name}\n\n"
        full_prompt += f"\n\n{get_prompt(self.tools)}"

        return full_prompt

    def format_messages(self, **kwargs: Any) -> List[BaseMessage]:
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

        input_message = HumanMessage(content=input_message)

        messages: List[BaseMessage] = [base_prompt, time_prompt]
        messages += historical_messages
        messages.append(input_message)
        logger.debug("all_prompt:", messages)
        return messages

    def process_chat_history(self, messages: List[dict]) -> List[BaseMessage]:
        results = []

        for message in messages:
            logger.debug(message)
            if message["type"] != "message" and message["type"] != "text":
                continue

            message_cls = AIMessage if message["user"] == self.ai_id else HumanMessage
            # replace the at in the message with the name of the bot
            text = message["text"].replace(f"@{self.ai_id}", f"@{self.ai_name}")
            results.append(message_cls(content=text))

        return results
