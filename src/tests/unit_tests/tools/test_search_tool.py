from sherpa_ai.config import AgentConfig
from sherpa_ai.output_parser import TaskAction
from sherpa_ai.tools import SearchTool


def test_formulate_search_query():
    config = AgentConfig(verbose=True)
    search_tool = SearchTool(config=config)
    query = "What is the weather today?"
    site = "https://www.google.com"

    search_query = search_tool.formulate_site_search(query, site)

    assert search_query == f"{query} site:{site}"

def test_search_query_includes_gsite_config():
    site = "https://www.google.com"
    config = AgentConfig(verbose=True, gsite=site)
    search_tool = SearchTool(config=config)

    query = "What is the weather today?"
    search_result = search_tool._run(query)
    assert search_result is not None
    assert search_result != ""


def test_search_query_includes_multiple_gsite_config():
    site = "https://www.google.com, https://www.langchain.com, https://openai.com"
    config = AgentConfig(
        verbose=True,
        gsite=site,
    )
    search_tool = SearchTool(config=config)
    query = "What is the weather today?"
    search_result = search_tool._run(query)
    assert search_result is not None
    assert search_result != ""


def test_search_query_includes_more_gsite_config_warning():
    site = "https://www.google.com, https://www.langchain.com, https://openai.com, https://www.google.com, https://www.langchain.com, https://openai.com"  # noqa: E501
    config = AgentConfig(
        verbose=True,
        gsite=site,
    )
    assert config.gsite == site.split(", ")
    search_tool = SearchTool(config=config)
    query = "What is the weather today?"
    search_result = search_tool._run(query)
    assert (
        "Warning: Only the first 5 URLs are taken into consideration." in search_result
    )


def test_search_query_includes_more_gsite_config_empty():
    site = ""
    config = AgentConfig(verbose=True, gsite=site)
    assert config.gsite == site.split(", ")
    search_tool = SearchTool(config=config)
    query = "What is the weather today?"
    search_result = search_tool._run(query)
    assert search_result is not None
    assert search_result != ""


def test_search_query_includes_invalid_url():
    site = "http://www.cwi.nl:80/%7Eguido/Python.html, /data/Python.html, 532, https://stackoverflow.com"  # noqa: E501
    invalid_domain_list = [
        "/data/Python.html",
        "532",
    ]
    config = AgentConfig(
        verbose=True,
        gsite=site,
    )
    assert config.gsite == site.split(", ")
    search_tool = SearchTool(config=config)
    query = "What is the weather today?"
    result = search_tool._run(query)

    invalid_domain = ", ".join(invalid_domain_list)
    expected_error = f"Warning: The doman {invalid_domain} is invalid and is not taken into consideration.\n"  # noqa: E501

    assert expected_error in result
