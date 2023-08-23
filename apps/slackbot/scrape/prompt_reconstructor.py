import config as cfg
from scrape.extract_github_readme import extract_github_readme
from utils import (
    chunk_and_summerize,
    count_string_tokens,
    get_link_from_slack_client_conversation,
    question_reconstructor,
    scarape_with_url,
)


class PromptReconstructor:
    def __init__(self, question, slack_message):
        self.question = question
        self.slack_message = slack_message

    def reconstruct_prompt(self):
        question = self.question
        last_message = self.slack_message
        last_message_links = get_link_from_slack_client_conversation(last_message)

        # if there is a link inside the question scrape then summerize based
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
                            "data": extract_github_readme(link),
                            "status": 200,
                        }
                    else:
                        scraped_data = {"data": "", "status": 404}
                else:
                    scraped_data = scarape_with_url(link)
                if scraped_data["status"] == 200:
                    chunk_summary = chunk_and_summerize(
                        link=link,
                        open_ai_key=cfg.OPENAI_API_KEY,
                        question=question,
                        text_data=scraped_data["data"],
                    )

                    while (
                        count_string_tokens(chunk_summary, "gpt-3.5-turbo")
                        > per_scrape_token_size
                    ):
                        chunk_summary = chunk_and_summerize(
                            link=link,
                            open_ai_key=cfg.OPENAI_API_KEY,
                            question=question,
                            text_data=chunk_summary,
                        )

                    final_summary.append({"data": chunk_summary, "link": link})

            question = question_reconstructor(question=question, data=final_summary)
        return question
