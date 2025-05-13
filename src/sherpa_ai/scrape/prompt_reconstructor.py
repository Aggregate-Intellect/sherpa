"""Prompt reconstruction module for Sherpa AI.

This module provides functionality for reconstructing prompts by incorporating
content from URLs mentioned in Slack messages. It handles scraping, summarizing,
and integrating web content into questions.
"""

import sherpa_ai.config as cfg
from sherpa_ai.scrape.extract_github_readme import extract_github_readme
from sherpa_ai.utils import (
    chunk_and_summarize,
    count_string_tokens,
    get_link_from_slack_client_conversation,
    rewrite_link_references,
    scrape_with_url,
)


class PromptReconstructor:
    """Prompt reconstructor for URL-enhanced questions.

    This class handles the process of enhancing questions by incorporating
    content from URLs mentioned in Slack messages. It scrapes the URLs,
    summarizes their content, and integrates the summaries into the
    original question.

    Attributes:
        question (str): The original question to be enhanced.
        slack_message (dict): Slack message containing URLs.
        llm (Any): Language model for text processing.

    Example:
        >>> reconstructor = PromptReconstructor(
        ...     question="How does this library work?",
        ...     slack_message={"text": "Check https://github.com/org/repo"},
        ...     llm=language_model
        ... )
        >>> enhanced = reconstructor.reconstruct_prompt()
        >>> print(enhanced)
        'Based on the GitHub repo...'
    """

    def __init__(self, question, slack_message, llm):
        """Initialize the prompt reconstructor.

        Args:
            question (str): The original question to be enhanced.
            slack_message (dict): Slack message containing URLs.
            llm (Any): Language model for text processing.
        """
        self.question = question
        self.slack_message = slack_message
        self.llm = llm

    def reconstruct_prompt(self):
        """Reconstruct the prompt by incorporating URL content.

        This method extracts URLs from the Slack message, scrapes their
        content, summarizes it while respecting token limits, and integrates
        the summaries into the original question.

        Returns:
            str: The enhanced question incorporating URL content summaries.

        Example:
            >>> reconstructor = PromptReconstructor(
            ...     question="How to use this?",
            ...     slack_message={"text": "See docs at https://docs.com"},
            ...     llm=language_model
            ... )
            >>> enhanced = reconstructor.reconstruct_prompt()
            >>> print(enhanced)
            'Based on the documentation at docs.com...'
        """
        question = self.question
        last_message = self.slack_message
        last_message_links = get_link_from_slack_client_conversation(last_message)

        # if there is a link inside the question scrape then summarize based
        # on question and then aggregate to the question
        if len(last_message_links) > 0:
            available_token = 3000 - count_string_tokens(question, "gpt-3.5-turbo")
            per_scrape_token_size = available_token / len(last_message_links)
            final_summary = []
            for last_message_link in last_message_links:
                link = last_message_link["url"]
                scraped_data = ""
                if "github" in last_message_links[-1]["base_url"]:
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
                        question=question,
                        text_data=scraped_data["data"],
                        llm=self.llm,
                    )

                    while (
                        count_string_tokens(chunk_summary, "gpt-3.5-turbo")
                        > per_scrape_token_size
                    ):
                        chunk_summary = chunk_and_summarize(
                            link=link,
                            question=question,
                            text_data=chunk_summary,
                            llm=self.llm,
                        )

                    final_summary.append({"data": chunk_summary, "link": link})

            question = rewrite_link_references(question=question, data=final_summary)
        return question
