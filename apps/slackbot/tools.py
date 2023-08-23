import os
from loguru import logger
from typing import Any

import requests
from bs4 import BeautifulSoup
from langchain import LLMChain
from langchain.prompts import Prompt
from langchain.tools import BaseTool
from langchain.utilities import GoogleSerperAPIWrapper
from langchain.vectorstores.base import VectorStoreRetriever
from typing_extensions import Literal

import config as cfg


def get_tools(memory):
    prompt = (
        "You are an assistant helping user solve the task. Perform the task as writen"
        "in the instruction.\nTask: {input}\nResult: "
    )
    prompt = Prompt.from_template(prompt)
    tools = []

    tools.append(ContextTool(memory=memory))

    if cfg.SERPER_API_KEY is not None:
        search_tool = SearchTool(api_wrapper=GoogleSerperAPIWrapper())
        tools.append(search_tool)
    else:
        logger.warning(
            "No SERPER_API_KEY found in environment variables, skipping SearchTool"
        )

    return tools


class SearchTool(BaseTool):
    name = "Search"
    description = (
        "Access the internet to search for the information. Only use this tool when "
        "you cannot find the information using internal search."
    )
    api_wrapper: GoogleSerperAPIWrapper

    def _run(self, query: str) -> str:
        google_serper = GoogleSerperAPIWrapper()
        search_results = google_serper._google_serper_api_results(query)

        # case 1: answerBox in the result dictionary
        if search_results.get("answerBox", False):
            answer_box = search_results.get("answerBox", {})
            if answer_box.get("answer"):
                answer = answer_box.get("answer")
            elif answer_box.get("snippet"):
                answer = answer_box.get("snippet").replace("\n", " ")
            elif answer_box.get("snippetHighlighted"):
                answer = answer_box.get("snippetHighlighted")
            title = search_results["organic"][0]["title"]
            link = search_results["organic"][0]["link"]

            return "Answer: " + answer + "\nLink:" + link

        # case 2: knowledgeGraph in the result dictionary
        snippets = []
        if search_results.get("knowledgeGraph", False):
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

        result = []
        for i in range(len(search_results["organic"][:10])):
            r = search_results["organic"][i]
            single_result = (
                "Description: " + r["title"] + r["snippet"] + "\nLink" + r["link"]
            )

            result.append(single_result)
        full_result = "\n".join(result)

        # answer = " ".join(snippets)
        if "knowledgeGraph" in search_results:
            answer = (
                "Description: "
                + search_results["knowledgeGraph"]["title"]
                + search_results["knowledgeGraph"]["description"]
                + "\nLink: "
                + search_results["knowledgeGraph"]["descriptionLink"]
            )
            full_result = answer + "\n" + full_result
        return full_result

    def _arun(self, query: str) -> str:
        raise NotImplementedError("SearchTool does not support async run")


class ContextTool(BaseTool):
    name = "Context Search"
    description = "Access internal documents for various information."
    memory: VectorStoreRetriever

    def _run(self, query: str) -> str:
        docs = self.memory.get_relevant_documents(query)
        result = ""
        for doc in docs:
            result += (
                "Document"
                + doc.page_content
                + "\nLink"
                + doc.metadata.get("source", "")
            )

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
