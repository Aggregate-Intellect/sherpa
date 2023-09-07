from typing import List

from langchain.chains import LLMChain
from langchain.llms.base import LLM
from langchain.prompts.base import BasePromptTemplate
from langchain.schema import BaseMessage
from langchain.tools.base import BaseTool
from langchain.vectorstores.base import VectorStoreRetriever

from sherpa_ai.action_planner.base import BaseActionPlanner
from sherpa_ai.prompt import SlackBotPrompt


class SelectiveActionPlanner(BaseActionPlanner):
    def __init__(
        self,
        llm: LLM,
        tools: List[BaseTool],
        ai_name: str = "SlackBot",
        ai_role: str = "Assistant",
    ):
        self.prompt = SlackBotPrompt(
            ai_name=ai_name,
            ai_role=ai_role,
            tools=tools,
            input_variables=["memory", "messages", "user_input", "task"],
            token_counter=llm.get_num_tokens,
        )
        self.chain = LLMChain(llm=llm, prompt=self.prompt)

    def select_action(
        self,
        previous_messages: List[BaseMessage],
        memory: VectorStoreRetriever,
        task: str = "",
        user_input: str = "",
    ) -> str:
        """
        Selects an action based on the previous messages and the user message.
        """
        return self.chain.run(
            task=task,
            messages=previous_messages,
            memory=memory,
            user_input=user_input,
        )
