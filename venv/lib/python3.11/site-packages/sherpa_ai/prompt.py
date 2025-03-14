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
    ai_name: str
    ai_role: str
    tools: List[BaseTool]
    token_counter: Callable[[str], int]
    send_token_limit: int = 4196

    def construct_base_prompt(self):
        full_prompt = f"You are a friendly assistent bot called"
        f" {self.ai_name}\n\n"
        full_prompt += f"\n\n{get_prompt(self.tools)}"
        logger.debug(full_prompt)
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
