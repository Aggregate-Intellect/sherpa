from sherpa_ai.config.task_config import AgentConfig
from sherpa_ai.models.sherpa_base_chat_model import SherpaChatOpenAI
from sherpa_ai.test_utils.llms import get_llm
from sherpa_ai.tools import LinkScraperTool
import sherpa_ai.config as cfg


def test_scraper_tool(get_llm):
    llm = get_llm(__file__, test_scraper_tool.__name__)

    scrape_tool = LinkScraperTool(llm=llm)
    query = "Summarize this link  https://en.wikipedia.org/wiki/Wikipedia?"

    result = scrape_tool._run(query)

    assert len(result) > 0
