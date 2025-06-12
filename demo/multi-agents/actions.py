from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from prompts import FOLLOW_UP_PROMPT, SUMMARY_PROMPT

from sherpa_ai.actions.base import AsyncBaseAction


class SearchAction(AsyncBaseAction):
    """An action that performs a search operation."""

    def __init__(self, query: str):
        """Initialize the SearchAction with a query string."""
        super().__init__()
        self.query = query

    async def execute(self):
        """Execute the search action asynchronously."""
        # Simulate an asynchronous search operation
        pass


class QuestionAction(AsyncBaseAction):
    """An action that asks a using follow-up questions."""

    llm: BaseChatModel
    count: int = 0

    async def execute(self):
        """Comes up with a follow-up question to the using using the context."""
        self.count += 1
        task = self.belief.get("task")
        conversation_context = self.belief.get("conversation_context", "")

        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("user", FOLLOW_UP_PROMPT),
            ]
        )

        output_parser = JsonOutputParser()

        chain = prompt_template | self.llm
        response_raw = await chain.arun(
            task=task, conversation_context=conversation_context
        )

        response = output_parser.parse(response_raw)
        question = response.get("question")

        conversation_context += f"\n<agent>\n{question}\n</agent>"

        human_response = input(question)
        conversation_context += f"\n<user>\n{human_response}\n</user>"
        self.belief["conversation_context"] = conversation_context

        return question, human_response
    
    def should_continue(self):
        """Determine if the action should continue based on the count."""
        return self.count < 3


class SummarizeAction(AsyncBaseAction):
    """An action that summarizes information."""

    llm: BaseChatModel

    async def execute(self):
        """Generate a summary based on the conversation context and task."""
        task = self.belief.get("task")
        conversation_context = self.belief.get("conversation_context", "")

        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("user", SUMMARY_PROMPT),
            ]
        )

        chain = prompt_template | self.llm
        response = await chain.arun(
            conversation_context=conversation_context, task=task
        )
        self.belief.set("summary", response)

        return response
