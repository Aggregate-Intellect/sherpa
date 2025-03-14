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
    """
    Scrapes the content of URLs mentioned in the given Slack message,
    and rewrites the question to incorporate a summary of the scraped URLs.
    """

    def __init__(self, question, slack_message, llm):
        """
        Initialize the PromptReconstructor with a question and a Slack message.

        Parameters:
        - question (str): question is a prompt to be used for prompt reconstruction.
        - slack_message (dict): The Slack message from which information is extracted.
        """

        self.question = question
        self.slack_message = slack_message
        self.llm = llm

    def reconstruct_prompt(self):
        """
        Reconstruct the prompt based on the question and the last Slack message.

        Parameters:
        - user_id (str, optional): User ID for context in prompt reconstruction.

        Returns:
        str: The reconstructed prompt .
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
