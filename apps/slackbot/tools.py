from typing import Any
from langchain import LLMChain
from langchain.tools import BaseTool
import requests
from bs4 import BeautifulSoup
from langchain.utilities import GoogleSerperAPIWrapper
from langchain.docstore.document import Document
from langchain.prompts import Prompt
from langchain.vectorstores.base import VectorStoreRetriever
from typing_extensions import Literal


def get_tools(memory):
    prompt = (
        "You are an assistant helping user solve the task. Perform the task as writen"
        "in the instruction.\nTask: {input}\nResult: "
    )
    prompt = Prompt.from_template(prompt)
    # llm_chain = LLMChain(llm=llm, prompt=prompt)
    search_tool = SearchTool(api_wrapper=GoogleSerperAPIWrapper())
    # llm_tool = LLMTool(llm_chain=llm_chain)

    # user_input_tool = UserInputTool()
    context_tool = ContextTool(memory=memory)

    return [search_tool, context_tool]


class ScrapeTool(BaseTool):
    name = "Scrape"
    description = "A tool for scraping a website for information."
    chunk_size = 200

    def _run(self, url: str) -> str:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        data = soup.get_text(strip=True)

        return data

    def _arun(self, *args: Any, **kwargs: Any):
        raise NotImplementedError("ScrapeTool does not support async run")


class SearchTool(BaseTool):
    name = "Search"
    description = (
        "Access the internet to search for the information, the input is a search query"
    )
    api_wrapper: GoogleSerperAPIWrapper

    def _run(self, query: str) -> str:
        google_serper = GoogleSerperAPIWrapper()
        search_results = google_serper._google_serper_api_results(query)
      
        # case 1: answerBox in the result dictionary
        if search_results.get("answerBox"):
            answer_box = search_results.get("answerBox", {})
            if answer_box.get("answer"):
                answer = answer_box.get("answer")
            elif answer_box.get("snippet"):
                answer = answer_box.get("snippet").replace("\n", " ")
            elif answer_box.get("snippetHighlighted"):
                answer = answer_box.get("snippetHighlighted")
            title = search_results["organic"][0]['title']
            link = search_results["organic"][0]['link']
            return "Answer: " + answer  + "\nLink:" + link
      
      # case 2: knowledgeGraph in the result dictionary
        snippets = []
        if search_results.get("knowledgeGraph"):
            kg = search_results.get("knowledgeGraph", {})
            title = kg.get("title")
            entity_type = kg.get("type")
            if entity_type:
                snippets.append(f"{title}: {entity_type}.")
            description = kg.get("description")
            if description:
                snippets.append(description)
            for attribute, value in kg.get("attributes", {}).items():
                snippets.append(f"{title} {attribute}: {value}.")
        k = 10
        search_type: Literal["news", "search", "places", "images"] = "search"
        result_key_for_type = {
        "news": "news",
        "places": "places",
        "images": "images",
        "search": "organic",
        }
        for result in search_results[result_key_for_type[search_type]][:k]:
            if "snippet" in result:
                snippets.append(result["snippet"])
            for attribute, value in result.get("attributes", {}).items():
                snippets.append(f"{attribute}: {value}.")

            if len(snippets) == 0:
                return ["No good Google Search Result was found"]

        answer = " ".join(snippets)
        title = search_results["organic"][0]['title']
        link = search_results["organic"][0]['link']
        return "Answer: " + answer + "\nTitle:" + title + "\nLink:" + link

    def _arun(self, query: str) -> str:
        raise NotImplementedError("SearchTool does not support async run")


class LLMTool(BaseTool):
    name = "LLM"
    description = (
        "Access the LLM to perform different tasks"
    )
    llm_chain: LLMChain

    def _run(self, query: str) -> str:
        return self.llm_chain.run(input=query)

    def _arun(self, query: str) -> str:
        raise NotImplementedError("LLMTool does not support async run")


class ContextTool(BaseTool):
    name = "Context"
    description = (
        "Access the read-only domain specific internal documents for the task."
        "You use this tool if you need further clarification of the task."
    )
    memory: VectorStoreRetriever

    def _run(self, query: str) -> str:
        docs = self.memory.get_relevant_documents(query)
        result = ""
        for doc in docs:
            result += "Document" + doc.page_content + "\nLink" + d.metadata.get("source", "")

        return result

    def _arun(self, query: str) -> str:
        raise NotImplementedError("ContextTool does not support async run")


class UserInputTool(BaseTool):
    name = "UserInput"
    description = (
        "Access the user input for the task."
        "You use this tool if you need further clarification of the task from the user."
    )

    def _run(self, query: str) -> str:
        return input(query)

    def _arun(self, query: str) -> str:
        raise NotImplementedError("UserInputTool does not support async run")