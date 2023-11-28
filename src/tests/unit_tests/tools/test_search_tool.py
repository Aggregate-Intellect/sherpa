from sherpa_ai.config import AgentConfig
from sherpa_ai.tools import SearchTool


def test_search_query_includes_gsite_config():
    site = "https://www.google.com"
    config = AgentConfig(
        verbose=True,
        gsite=site,
    )
    assert config.gsite == site
    search_tool = SearchTool(config=config)
    query = "What is the weather today?"

    search_result = search_tool._run(query)

    assert search_result is not None
    assert search_result is not ""


def test_search_query_includes_multiple_gsite_config():
    site = "https://www.google.com, https://www.langchain.com/, https://openai.com/"
    config = AgentConfig(
        verbose=True,
        gsite=site,
    )

    assert config.gsite == site

    search_tool = SearchTool(config=config)

    query = "What is the weather today?"

    search_result = search_tool._run(query)

    assert search_result is not None
    assert search_result is not ""

def test_search_query_includes_more_gsite_config_succeed():
    site = "https://www.google.com, https://www.langchain.com/, https://openai.com/, https://www.google.com, https://www.langchain.com/, https://openai.com/"
    config = AgentConfig(
        verbose=True,
        gsite=site,
    )

    assert config.gsite == site

    search_tool = SearchTool(config=config)

    query = "What is the weather today?"

    search_result = search_tool._run(query)

    assert "Warning: Only the first 5 URLs are taken into consideration." in search_result

def test_search_query_includes_more_gsite_config_failed():
    site = ""
    config = AgentConfig(
        verbose=True,
        gsite=site,
    )

    assert config.gsite == site

    search_tool = SearchTool(config=config)

    query = "What is the weather today?"

    search_result = search_tool._run(query)

    assert search_result is not None
    assert search_result is not ""
