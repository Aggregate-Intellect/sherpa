import re
import urllib.parse
from typing import Any, List, Tuple, Union

import requests
from langchain_community.utilities import GoogleSerperAPIWrapper 
from langchain_core.tools import BaseTool 
from langchain_core.vectorstores import VectorStoreRetriever 
from loguru import logger 
from typing_extensions import Literal 

import sherpa_ai.config as cfg
from sherpa_ai.config.task_config import AgentConfig


HTTP_GET_TIMEOUT = 2.5


def get_tools(memory, config):
    tools = []

    # tools.append(ContextTool(memory=memory))
    tools.append(UserInputTool())

    if cfg.SERPER_API_KEY is not None:
        search_tool = SearchTool(config=config)
        tools.append(search_tool)
    else:
        logger.warning(
            "No SERPER_API_KEY found in environment variables, skipping SearchTool"
        )

    return tools


class SearchArxivTool(BaseTool):
    name = "Arxiv Search"
    description = (
        "Access all the papers from Arxiv to search for domain-specific scientific publication."  # noqa: E501
        "Only use this tool when you need information in the scientific paper."
    )

    def _run(
        self, query: str, return_resources=False
    ) -> Union[str, Tuple[str, List[dict]]]:
        top_k = 10

        logger.debug(f"Search query: {query}")
        query = urllib.parse.quote_plus(query)
        url = (
            "http://export.arxiv.org/api/query?search_query=all:"
            + query.strip()
            + "&start=0&max_results="
            + str(top_k)
        )
        data = requests.get(url, timeout=HTTP_GET_TIMEOUT)
        xml_content = data.text

        summary_pattern = r"<summary>(.*?)</summary>"
        summaries = re.findall(summary_pattern, xml_content, re.DOTALL)
        title_pattern = r"<title>(.*?)</title>"
        titles = re.findall(title_pattern, xml_content, re.DOTALL)
        id_pattern = r"<id>(.*?)</id>"
        ids = re.findall(id_pattern, xml_content, re.DOTALL)

        result_list = []
        for i in range(len(titles)):
            result_list.append(
                "Title: " + titles[i] + "\n" + "Summary: " + summaries[i] + "\n"
            )
        result = "\n".join(result_list)

        # add resources for citation
        resources = []
        for i in range(len(titles)):
            resources.append(
                {
                    "Document": "Title: " + titles[i] + "\nSummary: " + summaries[i],
                    "Source": ids[i],
                }
            )

        logger.debug(f"Arxiv Search Result: {result_list}")

        if return_resources:
            return resources
        else:
            return result

    def _arun(self, query: str) -> str:
        raise NotImplementedError("SearchArxivTool does not support async run")


class SearchTool(BaseTool):
    name = "Search"
    config = AgentConfig()
    top_k: int = 10
    description = (
        "Access the internet to search for the information. Only use this tool when "
        "you cannot find the information using internal search."
    )

    def _run(self, query: str, return_resources=False) -> Union[str, List[dict]]:
        result = ""
        if self.config.search_domains:
            query_list = [
                self.formulate_site_search(query, str(i))
                for i in self.config.search_domains
            ]
            if len(query_list) >= 5:
                query_list = query_list[:5]
                logger.warning("Only the first 5 URLs are taken into consideration.")
        else:
            query_list = [query]
        if self.config.invalid_domains:
            invalid_domain_string = ", ".join(self.config.invalid_domains)
            logger.warning(
                f"The domain {invalid_domain_string} is invalid and is not taken into consideration."  # noqa: E501
            )

        top_k = int(self.top_k / len(query_list))
        if return_resources:
            resources = []

        for query in query_list:
            cur_result = self._run_single_query(query, top_k, return_resources)

            if return_resources:
                resources += cur_result
            else:
                result += "\n" + cur_result

        if return_resources:
            return resources
        else:
            return result

    def formulate_site_search(self, query: str, site: str) -> str:
        return query + " site:" + site

    def _run_single_query(
        self, query: str, top_k: int, return_resources=False
    ) -> Union[str, List[dict]]:
        logger.debug(f"Search query: {query}")
        google_serper = GoogleSerperAPIWrapper()
        search_results = google_serper._google_serper_api_results(query)
        logger.debug(f"Google Search Result: {search_results}")

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

            response = "Answer: " + answer
            meta = [{"Document": answer, "Source": link}]
            if return_resources:
                return meta
            else:
                return response + "\nLink:" + link

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

        search_type: Literal["news", "search", "places", "images"] = "search"
        result_key_for_type = {
            "news": "news",
            "places": "places",
            "images": "images",
            "search": "organic",
        }

        # case 3: general search results
        for result in search_results[result_key_for_type[search_type]][:top_k]:
            if "snippet" in result:
                snippets.append(result["snippet"])
            for attribute, value in result.get("attributes", {}).items():
                snippets.append(f"{attribute}: {value}.")

            if len(snippets) == 0:
                if return_resources:
                    return []
                else:
                    return "No good Google Search Result was found"

        result = []

        resources = []
        for i in range(len(search_results["organic"][:top_k])):
            r = search_results["organic"][i]
            single_result = r["title"] + r["snippet"]

            # If the links are not considered explicitly, add it to the search result
            # so that it can be considered by the LLM
            if not return_resources:
                single_result += "\nLink:" + r["link"]

            result.append(single_result)
            resources.append(
                {
                    "Document": "Description: " + r["title"] + r["snippet"],
                    "Source": r["link"],
                }
            )
        full_result = "\n".join(result)

        # answer = " ".join(snippets)
        if (
            "knowledgeGraph" in search_results
            and "description" in search_results["knowledgeGraph"]
            and "descriptionLink" in search_results["knowledgeGraph"]
        ):
            answer = (
                "Description: "
                + search_results["knowledgeGraph"]["title"]
                + search_results["knowledgeGraph"]["description"]
                + "\nLink:"
                + search_results["knowledgeGraph"]["descriptionLink"]
            )
            full_result = answer + "\n\n" + full_result
        if return_resources:
            return resources
        else:
            return full_result

    def _arun(self, query: str) -> str:
        raise NotImplementedError("SearchTool does not support async run")


class ContextTool(BaseTool):
    name = "Context Search"
    description = (
        "Access internal technical documentation for AI related projects, including"
        + "Fixie, LangChain, GPT index, GPTCache, GPT4ALL, autoGPT, db-GPT, AgentGPT, sherpa."  # noqa: E501
        + "Only use this tool if you need information for these projects specifically."
    )
    memory: VectorStoreRetriever

    def _run(
        self, query: str, return_resources=False
    ) -> Union[str, Tuple[str, List[dict]]]:
        docs = self.memory.get_relevant_documents(query)
        result = ""
        resources = []
        for doc in docs:
            result += (
                "Document"
                + doc.page_content
                + "\nLink:"
                + doc.metadata.get("source", "")
                + "\n"
            )
            if return_resources:
                resources.append(
                    {
                        "Document": doc.page_content,
                        "Source": doc.metadata.get("source", ""),
                    }
                )

        if return_resources:
            return resources
        else:
            return result

    def _arun(self, query: str) -> str:
        raise NotImplementedError("ContextTool does not support async run")


class UserInputTool(BaseTool):
    # TODO: Make an action for the user input
    name = "UserInput"
    description = (
        "Access the user input for the task."
        "You use this tool if you need more context and would like to ask clarifying questions to solve the task"  # noqa: E501
    )

    def _run(self, query: str) -> str:
        return input(query)

    def _arun(self, query: str) -> str:
        raise NotImplementedError("UserInputTool does not support async run")
