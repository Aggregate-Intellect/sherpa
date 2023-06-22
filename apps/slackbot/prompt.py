from pydantic import BaseModel
from langchain.prompts.chat import BaseChatPromptTemplate
from typing import Callable, Any, List
from langchain.schema import (
    BaseMessage, 
    HumanMessage, 
    SystemMessage,
    AIMessage
)
import time
from langchain.vectorstores.base import VectorStoreRetriever



class SlackBotPrompt(BaseChatPromptTemplate, BaseModel):
    ai_name: str
    ai_id: str
    token_counter: Callable[[str], int]
    send_token_limit: int = 4196

    def construct_base_prompt(self):
        full_prompt = (
            f"You are a friendly assistent bot called {self.ai_name}\n\n"
        )

        return full_prompt

    def format_messages(self, **kwargs: Any) -> List[BaseMessage]:
        base_prompt = SystemMessage(
            content=self.construct_base_prompt()
        )
        time_prompt = SystemMessage(
            content=f"The current time and date is {time.strftime('%c')}"
        )
        used_tokens = self.token_counter(base_prompt.content) + self.token_counter(
            time_prompt.content
        )

        query = kwargs["query"]
        retriever: VectorStoreRetriever = kwargs["retriever"]
        previous_messages = self.process_chat_history(kwargs["messages"])

        # retrieve relevant documents for the query
        relevant_docs = retriever.get_relevant_documents(query)
        relevant_memory = [d.page_content for d in relevant_docs]

        # remove documents from memory until the token limit is reached
        relevant_memory_tokens = sum(
            [self.token_counter(doc) for doc in relevant_memory]
        )
        while used_tokens + relevant_memory_tokens > 2500:
            relevant_memory = relevant_memory[:-1]
            relevant_memory_tokens = sum(
                [self.token_counter(doc) for doc in relevant_memory]
            )

        content_format = (
            f"Here are some documents that may be relevant to the topic:"
            f"\n{relevant_memory}\n\n"
        )
        input_message = (
            f"Use the above information to respond to the user's message:\n{query}\n\n"
        )

        # print(content_format)

        memory_message = SystemMessage(content=content_format)
        used_tokens += self.token_counter(memory_message.content)
        historical_messages: List[BaseMessage] = []
        print(previous_messages)
        for message in previous_messages[-10:][::-1]:
            message_tokens = self.token_counter(message.content)
            if used_tokens + message_tokens > self.send_token_limit - 1000:
                break
            historical_messages = [message] + historical_messages
            used_tokens += message_tokens
        print(historical_messages)

        input_message = HumanMessage(content=input_message)

        messages: List[BaseMessage] = [base_prompt, time_prompt, memory_message]
        messages += historical_messages
        messages.append(input_message)

        return messages
    
    def process_chat_history(self, messages: List[dict]) -> List[BaseMessage]:
        results = []

        for message in messages:
            print(message)
            if message['type'] != 'message' and message['type'] != 'text':
                continue
        
            message_cls = AIMessage if message['user'] == self.ai_id else HumanMessage
            # replace the at in the message with the name of the bot
            text = message['text'].replace(f'@{self.ai_id}', f'@{self.ai_name}')
            results.append(message_cls(content=text))
        
        return results

