from pydantic import BaseModel
from langchain.prompts.chat import BaseChatPromptTemplate
from typing import Callable, Any, List
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
import time
from langchain.vectorstores.base import VectorStoreRetriever



class SlackBotPrompt(BaseChatPromptTemplate, BaseModel):
    ai_name: str
    token_counter: Callable[[str], int]
    send_token_limit: int = 4196

    def construct_base_prompt(self):
        full_prompt = (
            f"You are a friendly assistent bot called {self.ai_name}\n\n"
        )

        return full_prompt

    def format_messages(self, **kwags: Any) -> List[BaseMessage]:
        base_prompt = SystemMessage(
            content=self.construct_full_prompt()
        )
        time_prompt = SystemMessage(
            content=f"The current time and date is {time.strftime('%c')}"
        )
        used_tokens = self.token_counter(base_prompt.content) + self.token_counter(
            time_prompt.content
        )

        retriever: VectorStoreRetriever = kwargs["retriever"]

        return message
    
    def process_chat_history(self, messages: List[dict]) -> List[BaseMessage]:
        return messages
