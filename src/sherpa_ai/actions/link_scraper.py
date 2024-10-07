from typing import Any
from sherpa_ai.actions.base import BaseAction
from sherpa_ai.tools import LinkScraperTool
from pydantic import BaseModel, Field


class LinkScraperAction(BaseAction, BaseModel):
    llm: Any
    name: str = "Link Scraper"
    args: dict = {
        "url": "the url to be scrapped",
    }
    usage: str = "Simple link scraper that scrapes the data from url and returns string"
    scraper_tool: LinkScraperTool = Field(default_factory=LinkScraperTool)
    print(scraper_tool)

    def execute(self, url: str, **kwargs) -> str:
        """
        Executes the scraper tool and returns the scraped data.
        Args:
            url: The url to be scrapped
        Returns:
            str: The data scrapped from the url
        """
        try:
            result = self.scraper_tool._run(url,self.llm)
            if not result or len(result) == 0:
                raise ValueError("Scraper returned no content.")
            return str(result)
        except Exception as e:
            print(f"Error during scraping: {e}")
            return ""