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
from sherpa_ai.scrape.extract_github_readme import extract_github_readme
from sherpa_ai.utils import (chunk_and_summarize, count_string_tokens,
                             get_links_from_text, rewrite_link_references,
                             scrape_with_url)

HTTP_GET_TIMEOUT = 20.0


def get_tools(memory, config):
    """Factory function to create and configure a set of tools for the agent.

    This function creates and returns a list of tools that the agent can use,
    including search tools and user input handling. The tools are configured
    based on the provided memory and configuration parameters.

    Args:
        memory: The memory component for tools that require memory access.
        config: Configuration object containing tool settings.

    Returns:
        List[BaseTool]: A list of configured tool instances.

    Example:
        >>> from sherpa_ai.tools import get_tools
        >>> tools = get_tools(memory=memory, config=config)
        >>> for tool in tools:
        ...     print(tool.name)
        UserInput
        Search
    """
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
    """Tool for searching and retrieving scientific papers from Arxiv.

    This class provides functionality to search Arxiv's database for scientific papers
    and retrieve their titles, summaries, and IDs. It's particularly useful for
    research-related queries and academic information gathering.

    This class inherits from :class:`BaseTool` and provides methods to:
        - Search Arxiv's database
        - Parse and format search results
        - Return paper metadata and summaries

    Attributes:
        name (str): The name of the tool, set to "Arxiv Search".
        description (str): A description of when to use this tool.

    Example:
        >>> from sherpa_ai.tools import SearchArxivTool
        >>> tool = SearchArxivTool()
        >>> result = tool._run("machine learning")
        >>> print(result)
        Title: Example Paper
        Summary: This paper discusses...
    """

    name: str = "Arxiv Search"
    description: str = (
        "Access all the papers from Arxiv to search for domain-specific scientific publication."  # noqa: E501
        "Only use this tool when you need information in the scientific paper."
    )

    def _run(
        self, query: str, return_resources=False
    ) -> Union[str, Tuple[str, List[dict]]]:
        """Execute the Arxiv search with the given query.

        Args:
            query (str): The search query to find papers.
            return_resources (bool, optional): Whether to return resources for citation.
                Defaults to False.

        Returns:
            Union[str, Tuple[str, List[dict]]]: Either a formatted string of results
                or a tuple containing the results and resource list for citation.

        Example:
            >>> tool = SearchArxivTool()
            >>> result = tool._run("neural networks")
            >>> print(result)
            Title: Neural Networks in Practice
            Summary: This paper explores...
        """
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
        """Asynchronous version of the run method (not implemented).

        Args:
            query (str): The search query.

        Raises:
            NotImplementedError: This method is not supported.
        """
        raise NotImplementedError("SearchArxivTool does not support async run")


class SearchTool(BaseTool):
    """Tool for performing internet searches using the Google Serper API.

    This class provides functionality to search the internet for information using
    the Google Serper API. It supports domain-specific searches and can return
    both formatted results and resources for citation.

    This class inherits from :class:`BaseTool` and provides methods to:
        - Perform general internet searches
        - Execute domain-specific searches
        - Parse and format search results
        - Handle knowledge graph and answer box results

    Attributes:
        name (str): The name of the tool, set to "Search".
        config (AgentConfig): Configuration object for search settings.
        top_k (int): Number of results to return, defaults to 10.
        description (str): A description of when to use this tool.

    Example:
        >>> from sherpa_ai.tools import SearchTool
        >>> tool = SearchTool(config=config)
        >>> result = tool._run("python programming")
        >>> print(result)
        Answer: Python is a high-level programming language...
    """

    name: str = "Search"
    config: AgentConfig = AgentConfig()
    top_k: int = 10
    description: str = (
        "Access the internet to search for the information. Only use this tool when "
        "you cannot find the information using internal search."
    )

    def _run(self, query: str, return_resources=False) -> Union[str, List[dict]]:
        """Execute the search with the given query.

        This method handles both general and domain-specific searches, processing
        the results and returning them in the requested format.

        Args:
            query (str): The search query.
            return_resources (bool, optional): Whether to return resources for citation.
                Defaults to False.

        Returns:
            Union[str, List[dict]]: Either a formatted string of results or a list
                of resources for citation.

        Example:
            >>> tool = SearchTool(config=config)
            >>> result = tool._run("python tutorials")
            >>> print(result)
            Answer: Python tutorials for beginners...
            Link: https://example.com/tutorials
        """
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
        """Formulate a site-specific search query.

        Args:
            query (str): The base search query.
            site (str): The site to restrict the search to.

        Returns:
            str: The formatted site-specific search query.

        Example:
            >>> tool = SearchTool()
            >>> query = tool.formulate_site_search("python", "python.org")
            >>> print(query)
            python site:python.org
        """
        return query + " site:" + site

    def _run_single_query(
        self, query: str, top_k: int, return_resources=False
    ) -> Union[str, List[dict]]:
        """Execute a single search query and process its results.

        This method handles different types of search results including answer boxes,
        knowledge graphs, and general search results.

        Args:
            query (str): The search query to execute.
            top_k (int): Number of results to return.
            return_resources (bool, optional): Whether to return resources for citation.
                Defaults to False.

        Returns:
            Union[str, List[dict]]: Either a formatted string of results or a list
                of resources for citation.

        Example:
            >>> tool = SearchTool()
            >>> result = tool._run_single_query("python programming", top_k=5)
            >>> print(result)
            Answer: Python is a versatile programming language...
            Link: https://example.com/python
        """
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
        """Asynchronous version of the run method (not implemented).

        Args:
            query (str): The search query.

        Raises:
            NotImplementedError: This method is not supported.
        """
        raise NotImplementedError("SearchTool does not support async run")


class ContextTool(BaseTool):
    """Tool for accessing internal technical documentation.

    This class provides functionality to search and retrieve information from internal
    technical documentation for various AI-related projects. It uses a vector store
    retriever to find relevant documentation based on queries.

    This class inherits from :class:`BaseTool` and provides methods to:
        - Search internal documentation
        - Retrieve relevant context
        - Format search results

    Attributes:
        name (str): The name of the tool, set to "Context".
        description (str): A description of when to use this tool.
        memory (VectorStoreRetriever): The vector store retriever for searching documentation.

    Example:
        >>> from sherpa_ai.tools import ContextTool
        >>> tool = ContextTool(memory=memory)
        >>> result = tool._run("How to use LangChain?")
        >>> print(result)
        LangChain is a framework for developing applications...
    """

    name: str = "Context"
    description: str = (
        "Access internal technical documentation for AI related projects, including"
        + "Fixie, LangChain, GPT index, GPTCache, GPT4ALL, autoGPT, db-GPT, AgentGPT, sherpa."  # noqa: E501
        + "Only use this tool if you need information for these projects specifically."
    )
    memory: VectorStoreRetriever

    def _run(
        self, query: str, return_resources=False
    ) -> Union[str, Tuple[str, List[dict]]]:
        """Execute the context search with the given query.

        Args:
            query (str): The search query.
            return_resources (bool, optional): Whether to return resources for citation.
                Defaults to False.

        Returns:
            Union[str, Tuple[str, List[dict]]]: Either a formatted string of results
                or a tuple containing the results and resource list for citation.

        Example:
            >>> tool = ContextTool(memory=memory)
            >>> result = tool._run("LangChain documentation")
            >>> print(result)
            LangChain is a framework...
        """
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
        """Asynchronous version of the run method (not implemented).

        Args:
            query (str): The search query.

        Raises:
            NotImplementedError: This method is not supported.
        """
        raise NotImplementedError("ContextTool does not support async run")


class UserInputTool(BaseTool):
    """Tool for handling user input in the agent system.

    This class provides functionality to process and handle user input within the
    agent system. It serves as an interface for receiving and processing user queries.

    This class inherits from :class:`BaseTool` and provides methods to:
        - Process user input
        - Return user queries

    Attributes:
        name (str): The name of the tool, set to "UserInput".
        description (str): A description of when to use this tool.

    Example:
        >>> from sherpa_ai.tools import UserInputTool
        >>> tool = UserInputTool()
        >>> result = tool._run("What is Python?")
        >>> print(result)
        What is Python?
    """

    # TODO: Make an action for the user input
    name: str = "UserInput"
    description: str = (
        "Use this tool when you need to get input from the user. "
        "The input will be passed to the user and the response will be returned."
    )

    def _run(self, query: str) -> str:
        """Process and return the user input.

        Args:
            query (str): The user's input query.

        Returns:
            str: The processed user input.

        Example:
            >>> tool = UserInputTool()
            >>> result = tool._run("Tell me about Python")
            >>> print(result)
            Tell me about Python
        """
        return input(query)

    def _arun(self, query: str) -> str:
        """Asynchronous version of the run method (not implemented).

        Args:
            query (str): The user's input query.

        Raises:
            NotImplementedError: This method is not supported.
        """
        raise NotImplementedError("UserInputTool does not support async run")


class LinkScraperTool(BaseTool):
    """Tool for extracting content from web links.

    This class provides functionality to scrape and extract content from web links.
    It's useful for retrieving information from specific URLs when needed.

    This class inherits from :class:`BaseTool` and provides methods to:
        - Scrape web content
        - Extract information from links
        - Process and format scraped content

    Attributes:
        name (str): The name of the tool, set to "Link Scraper".
        description (str): A description of when to use this tool.

    Example:
        >>> from sherpa_ai.tools import LinkScraperTool
        >>> tool = LinkScraperTool()
        >>> result = tool._run("https://example.com", llm=llm)
        >>> print(result)
        Content from the webpage...
    """

    name: str = "Link Scraper"
    description: str = "Access the content of a link. Only use this tool when you need to extract information from a link."

    def _run(
        self,
        query: str,
        llm: Any,
    ) -> str:
        """Scrape and extract content from a web link.

        Args:
            query (str): The URL to scrape.
            llm (Any): The language model to use for processing.

        Returns:
            str: The processed user input.

        Example:
            >>> tool = LinkScraperTool()
            >>> result = tool._run("https://example.com", llm=llm)
            >>> print(result)
            Content from the webpage...
        """
        query_links = get_links_from_text(query)
        # if there is a link inside the question scrape then summarize based
        # on question and then aggregate to the question

        if len(query_links) > 0:
            # TODO I should get gpt-3.5-turbo from an environment variable or a config file
            available_token = 3000 - count_string_tokens(query, "gpt-3.5-turbo")
            per_scrape_token_size = available_token / len(query_links)
            final_summary = []
            for last_message_link in query_links:
                link = last_message_link["url"]
                scraped_data = ""
                if "github" in query_links[-1]["base_url"]:
                    git_scraper = extract_github_readme(link)
                    if git_scraper:
                        scraped_data = {
                            "data": git_scraper,
                            "status": 200,
                        }
                    else:
                        scraped_data = {"data": "", "status": 404}
                else:
                    scraped_data = scrape_with_url(link)
                if scraped_data["status"] == 200:
                    chunk_summary = chunk_and_summarize(
                        link=link,
                        question=query,
                        text_data=scraped_data["data"],
                        # TODO_ user id is not going to be needed here in the future
                        # user_id="",
                        llm=llm,
                    )

                    while (
                        count_string_tokens(chunk_summary, "gpt-3.5-turbo")
                        > per_scrape_token_size
                    ):
                        chunk_summary = chunk_and_summarize(
                            link=link,
                            question=query,
                            text_data=chunk_summary,
                            # user_id="",
                            llm=llm,
                        )

                    final_summary.append({"data": chunk_summary, "link": link})
                else:
                    final_summary.append({"data": "Scraping failed", "link": link})

            scraped_data = rewrite_link_references(question=query, data=final_summary)
            resources = []
            resources.append(
                {
                    "Document": scraped_data,
                    "Source": ", ".join([link["url"] for link in query_links]),
                }
            )
        return resources

    def _arun(self, query: str) -> str:
        """Asynchronous version of the run method (not implemented).

        Args:
            query (str): The URL to scrape.

        Raises:
            NotImplementedError: This method is not supported.
        """
        raise NotImplementedError("LinkScraperTool does not support async run")
