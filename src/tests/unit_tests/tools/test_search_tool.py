import re
from unittest.mock import MagicMock, patch

import pytest
from loguru import logger

import sherpa_ai.config as cfg
from sherpa_ai.config import AgentConfig
from sherpa_ai.tools import GoogleSerperAPIWrapper, SearchTool

# Captured at collection time, before the autouse `mock_env` fixture (conftest.py)
# patches GoogleSerperAPIWrapper.search for every test.
_real_search = GoogleSerperAPIWrapper.search


def _extract_links(search_result: str) -> list:
    """Pull every `Link:<url>` field value out of a formatted search
    result, so tests can assert on the parsed link tokens directly
    instead of doing a raw substring/containment check against the whole
    text blob."""
    return re.findall(r"Link:(\S+)", search_result)


def test_google_serper_search_calls_serper_api_directly():
    """Regression test for the langchain-community removal: this hits
    Serper's API directly (no GoogleSerperAPIWrapper in between), so pin
    down the request shape it relies on."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"organic": []}

    with patch.object(cfg, "SERPER_API_KEY", "test-key"), \
         patch("sherpa_ai.tools.requests.post", return_value=mock_response) as mock_post:
        result = _real_search(GoogleSerperAPIWrapper(), "what is the weather today?")

    mock_post.assert_called_once_with(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": "test-key", "Content-Type": "application/json"},
        params={"q": "what is the weather today?"},
        timeout=pytest.approx(20.0),
    )
    mock_response.raise_for_status.assert_called_once()
    assert result == {"organic": []}


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
    # The mocked Serper response (see conftest.GOOGLE_SEARCH_MOCK) must actually
    # flow through the result parsing: title, snippet and link should survive.
    # Exact equality (not substring containment) so CodeQL does not mistake this
    # for URL sanitization logic.
    assert "Google is a search engine" in search_result
    assert _extract_links(search_result) == ["https://www.google.com"]


def test_search_query_includes_multiple_gsite_config():
    site = "https://www.google.com, https://www.langchain.com, https://openai.com"
    config = AgentConfig(
        verbose=True,
        gsite=site,
    )
    search_tool = SearchTool(config=config)
    query = "What is the weather today?"
    search_result = search_tool._run(query)
    # One mocked organic result per site-restricted query must be parsed through:
    # the static mock returns the same single link for each of the site queries.
    assert search_result.count("Google is a search engine") == len(site.split(", "))
    assert _extract_links(search_result) == ["https://www.google.com"] * len(
        site.split(", ")
    )


def test_search_returns_resources_for_citation():
    config = AgentConfig(verbose=True)
    search_tool = SearchTool(config=config)
    resources = search_tool._run("What is the weather today?", return_resources=True)

    # The resource contract (Document/Source keys) is relied on by citation
    # validation and retrieval actions; verify the mocked search result is
    # mapped into it correctly.
    assert isinstance(resources, list)
    assert len(resources) == 1
    assert resources[0]["Document"] == "Description: GoogleGoogle is a search engine"
    assert resources[0]["Source"] == "https://www.google.com"


@pytest.fixture
def mock_logger():
    with patch("loguru.logger.warning") as mock_logger:
        yield mock_logger


def test_search_query_includes_more_gsite_config_warning(mock_logger):
    site = "https://www.google.com, https://www.langchain.com, https://openai.com, https://www.google.com, https://www.langchain.com, https://openai.com"  # noqa: E501
    config = AgentConfig(
        verbose=True,
        gsite=site,
    )
    assert config.gsite == site.split(", ")
    search_tool = SearchTool(config=config)
    query = "What is the weather today?"
    search_tool._run(query)

    expected_warning = "Only the first 5 URLs are taken into consideration."
    mock_logger.assert_called_with(expected_warning)


def test_search_query_includes_more_gsite_config_empty():
    site = ""
    config = AgentConfig(verbose=True, gsite=site)
    assert config.gsite == site.split(", ")
    search_tool = SearchTool(config=config)
    query = "What is the weather today?"
    search_result = search_tool._run(query)
    # Empty gsite means a single unrestricted query, so exactly one mocked link.
    assert "Google is a search engine" in search_result
    assert _extract_links(search_result) == ["https://www.google.com"]


def test_search_query_includes_invalid_url(mock_logger):
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
    search_tool._run(query)

    invalid_domain = ", ".join(invalid_domain_list)
    expected_error = f"The domain {invalid_domain} is invalid and is not taken into consideration."  # noqa: E501

    logger.warning.assert_called_with(expected_error)
