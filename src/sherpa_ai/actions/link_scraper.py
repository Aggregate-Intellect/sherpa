from typing import Any
from sherpa_ai.actions.base import BaseAction
from sherpa_ai.tools import LinkScraperTool
from pydantic import BaseModel, Field


class LinkScraperAction(BaseAction, BaseModel):
    """A class for scraping content from web URLs.
    
    This class provides functionality to scrape and extract content from web pages
    using a specialized scraping tool. It handles URL validation, content extraction,
    and error handling for web scraping operations.
    
    This class inherits from both :class:`BaseAction` and :class:`BaseModel` and provides:
      - URL content scraping
      - Error handling for failed scrapes
      - Content validation
    
    Attributes:
        llm (Any): Language model used for processing scraped content.
        name (str): Name of the action, set to "Link Scraper".
        args (dict): Arguments accepted by the action, including "url".
        usage (str): Description of the action's usage.
        scraper_tool (LinkScraperTool): Tool for performing web scraping operations.
    
    Example:
        >>> from sherpa_ai.actions import LinkScraperAction
        >>> scraper = LinkScraperAction(llm=my_llm)
        >>> content = scraper.execute(url="https://example.com")
        >>> print(content)
    """
    llm: Any
    name: str = "Link Scraper"
    args: dict = {
        "url": "the url to be scrapped",
    }
    usage: str = "Simple link scraper that scrapes the data from url and returns string"
    scraper_tool: LinkScraperTool = Field(default_factory=LinkScraperTool)

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
            return ""