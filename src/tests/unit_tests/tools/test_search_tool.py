


from sherpa_ai.config import AgentConfig
from sherpa_ai.tools import SearchTool
from sherpa_ai.output_parser import TaskAction


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
    site = "https://www.google.com, https://www.langchain.com, https://openai.com"
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

def test_search_query_includes_more_gsite_config_warning():
    site = "https://www.google.com, https://www.langchain.com, https://openai.com, https://www.google.com, https://www.langchain.com, https://openai.com"
    config = AgentConfig(
        verbose=True,
        gsite=site,
    )
    assert config.gsite == site
    search_tool = SearchTool(config=config)
    query = "What is the weather today?"
    search_result = search_tool._run(query)
    assert "Warning: Only the first 5 URLs are taken into consideration." in search_result

def test_search_query_includes_more_gsite_config_empty():
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

def test_search_query_includes_invalid_url():
    site = "http://www.cwi.nl:80/%7Eguido/Python.html, /data/Python.html, 532, https://stackoverflow.com"
    config = AgentConfig(
        verbose=True,
        gsite=site,
    )
    assert config.gsite == site
    search_tool = SearchTool(config=config)
    query = "What is the weather today?"
    error = search_tool._run(query)

    expected_error = TaskAction(
                name="ERROR",
                args={"error": f"The input URL is not valid"},
            )
    assert error == expected_error

def test_search_query_invalid_format():
    site = "https://www.google.com,https://www.langchain.com,https://openai.com"
    config = AgentConfig(
        verbose=True,
        gsite=site,
    )
    assert config.gsite == site
    search_tool = SearchTool(config=config)
    query = "What is the weather today?"
    search_result = search_tool._run(query)

    expected_result = TaskAction(
                    name="ERROR",
                    args={"error": f"Could not process invalid website URLs format. Split urls with ', "},
                )
    assert search_result is not None
    assert search_result == expected_result
    

