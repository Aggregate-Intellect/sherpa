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
from tools import BaseTool
from prompt_generator import get_prompt



class SlackBotPrompt(BaseChatPromptTemplate, BaseModel):
    ai_name: str
    ai_role: str
    tools:List[BaseTool]
    token_counter: Callable[[str], int]
    send_token_limit: int = 4196

    def construct_base_prompt(self):
        full_prompt = (
            f"You are a friendly assistent bot called {self.ai_name}\n\n"
        )
        full_prompt += f"\n\n{get_prompt(self.tools)}"

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

        query = kwargs["task"]
        retriever: VectorStoreRetriever = kwargs["memory"]
        previous_messages = kwargs["messages"]

        # retrieve relevant documents for the query
        # relevant_docs = retriever.get_relevant_documents(query)
        
        # relevant_memory = ["Document: " + d.page_content + "\nLink" + d.metadata.get("source", "") + "\n" for d in relevant_docs]

        # # remove documents from memory until the token limit is reached
        # relevant_memory_tokens = sum(
        #     [self.token_counter(doc) for doc in relevant_memory]
        # )
        # while used_tokens + relevant_memory_tokens > 2500:
        #     relevant_memory = relevant_memory[:-1]
        #     relevant_memory_tokens = sum(
        #         [self.token_counter(doc) for doc in relevant_memory]
        #     )

        # content_format = (
        #     f"Here are some documents that may be relevant to the topic:"
        #     f"\n{relevant_memory}\n\n"
        # )

        # input_message = (
        #     f"Use the above information to respond to the user's message:\n{query}\n\n"
        #     f"If you use any resource, then create inline citation by adding the source link of the reference document at the of the sentence."
        #     f"Only use the link given in the reference document. DO NOT create link by yourself. DO NOT include citation if the resource is not necessary. "
        # )
        
        input_message = f'Current task: {query} \n {kwargs["user_input"]}'


        # print(content_format)

        # memory_message = SystemMessage(content=content_format)
        # used_tokens += self.token_counter(memory_message.content)
        historical_messages: List[BaseMessage] = []
        # print(previous_messages)
        for message in previous_messages[-10:][::-1]:
            message_tokens = self.token_counter(message.content)
            if used_tokens + message_tokens > self.send_token_limit - 1000:
                break
            historical_messages = [message] + historical_messages
            used_tokens += message_tokens
        # print(historical_messages)

        input_message = HumanMessage(content=input_message)

        messages: List[BaseMessage] = [base_prompt, time_prompt]
        messages += historical_messages
        messages.append(input_message)
        print("all_prompt:", previous_messages)
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

