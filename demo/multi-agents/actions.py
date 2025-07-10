import re

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger
from prompts import (FOLLOW_UP_PROMPT, SEARCH_PROMPT, SUMMARIZE_SEARCH_PROMPT,
                     SUMMARY_PROMPT)

from sherpa_ai.actions.base import AsyncBaseAction
from sherpa_ai.memory import SharedMemory
from sherpa_ai.tools import SearchTool


def extract_json(text: str) -> dict:
    """Extract JSON from a string."""
    try:
        # Use regex to find the markdown JSON block
        match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL | re.MULTILINE)
        if match:
            json_str = match.group(1).strip()
            # Parse the JSON string
            return JsonOutputParser().parse(json_str)
    except Exception as e:
        logger.error(f"Error extracting JSON: {e}")
        return {}


class SearchAction(AsyncBaseAction):
    """An action that performs a search operation."""

    tool: SearchTool = None
    top_k: int = 10
    llm: BaseChatModel
    shared_memory: SharedMemory

    def __init__(self, **kwargs):
        """Initialize the SearchAction with a SearchTool."""
        super().__init__(**kwargs)
        self.tool = SearchTool(top_k=self.top_k)

    async def execute(self, conversation_context):
        """Execute the search action asynchronously."""
        # Simulate an asynchronous search operation
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("user", SEARCH_PROMPT),
            ]
        )

        logger.info(prompt_template)
        task = self.belief.get("task")
        chain = prompt_template | self.llm
        response_raw = await chain.ainvoke(
            input={"task": task, "conversation_context": conversation_context}
        )
        response = extract_json(response_raw.content)
        query = response.get("query")
        logger.info(f"Search query: {query}")

        resources = self.tool._run(query, return_resources=True)

        logger.info(resources)
        await self.shared_memory.async_add(
            event_type="search_results",
            name="results",
            content=resources,
        )


class QuestionAction(AsyncBaseAction):
    """An action that asks a using follow-up questions."""

    name: str = "QuestionAction"
    usage: str = "An action that asks follow-up questions to the user."
    shared_memory: SharedMemory
    args: dict = {}

    llm: BaseChatModel
    count: int = 0

    async def get_search_summary(self, search_results: str):
        """Generate a summary of the search results."""
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("user", SUMMARIZE_SEARCH_PROMPT),
            ]
        )

        chain = prompt_template | self.llm
        response = await chain.ainvoke(input={"search_results": search_results})
        return response

    async def execute(
        self,
    ):
        """Comes up with a follow-up question to the using using the context."""
        self.count += 1
        task = self.belief.get("task")
        conversation_context = self.belief.get("conversation_context", "")

        search_events = self.belief.get_by_type("search_results")
        if len(search_events) > 0:
            # If there is a new observation, summarize it
            search_results = search_events[-1].content
            summary = await self.get_search_summary(search_results)
            conversation_context += f"\n<search>\n{summary}\n</search>"

        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("user", FOLLOW_UP_PROMPT),
            ]
        )

        logger.info(conversation_context)
        
        await self.shared_memory.async_add(
            event_type="trigger",
            name="perform_search",
            args={
                "conversation_context": conversation_context,
            },
        )

        chain = prompt_template | self.llm
        response_raw = await chain.ainvoke(
            input={"task": task, "conversation_context": conversation_context}
        )

        logger.info(f"Response raw: {response_raw.content}")
        response = extract_json(response_raw.content)
        logger.info(f"Response parsed: {response}")
        question = response.get("question")

        conversation_context += f"\n<agent>\n{question}\n</agent>"

        human_response = input(question)
        conversation_context += f"\n<user>\n{human_response}\n</user>"
        self.belief.set("conversation_context", conversation_context)

        return question, human_response

    def should_continue(self):
        """Determine if the action should continue based on the count."""
        return self.count < 3


class SummarizeAction(AsyncBaseAction):
    """An action that summarizes information."""

    name: str = "SummarizeAction"
    usage: str = "An action that summarizes the conversation context."
    args: dict = {}

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
        response = await chain.ainvoke(
            input={"conversation_context": conversation_context, "task": task}
        )
        self.belief.set("summary", response.content)

        return response
