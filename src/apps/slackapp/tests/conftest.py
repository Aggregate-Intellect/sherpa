import os
from unittest import mock

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--external_api",
        action="store_true",
        default=False,
        help="run the test with actual external API calls",
    )


@pytest.fixture
def external_api(request):
    return request.config.getoption("--external_api")


GOOGLE_SEARCH_MOCK = {
    "organic": [
        {
            "title": "Google",
            "snippet": "Google is a search engine",
            "link": "https://www.google.com",
        }
    ],
}


def guard(*args, **kwargs):
    raise Exception("I told you not to use the Internet!")


@pytest.fixture(autouse=True)
def mock_env(external_api):
    # if run with external_api, don't mock the environment
    if external_api:
        return

    # Set a dummy API key to avoid Pydantic validation error from langchain
    os.environ["SERPER_API_KEY"] = "dummy"
    os.environ["OPENAI_API_KEY"] = "dummy"

    with mock.patch(
        "langchain.utilities.GoogleSerperAPIWrapper._google_serper_api_results"
    ) as mock_search, mock.patch("sherpa_ai.utils.scrape_with_url") as mock_scrape:
        mock_search.return_value = GOOGLE_SEARCH_MOCK
        # mock_socket.side_effect = guard
        mock_scrape.return_value = {"data": "", "status": 200}
        yield
