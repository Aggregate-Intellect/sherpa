from unittest.mock import patch

import pytest

from sherpa_ai.actions.google_search import GoogleSearch
from sherpa_ai.actions.reranking import RerankingByQuery


Resources = [
    {"Document": "0", "Source": "www.link1.com"},
    {"Document": "1", "Source": "www.link2.com"},
    {"Document": "2", "Source": "www.link3.com"},
]


@pytest.fixture
def mock_google_search():
    with patch("sherpa_ai.actions.GoogleSearch.search") as mock_google_search:
        mock_google_search.return_value = Resources
        yield mock_google_search


@pytest.fixture
def mock_embedding_func():
    def embedding(text):
        return_values = [[1, 0, 0], [1, 1, 1], [1, 1, 0]]
        return return_values[int(text)]

    return embedding


def test_default_reranker(mock_google_search, mock_embedding_func):
    reranker = RerankingByQuery(embedding_func=mock_embedding_func)

    action = GoogleSearch(
        role_description="Planner",
        task="What is AutoGPT?",
        llm=None,  # LLM is not used since we are mocking the search
        perform_reranking=True,
        reranker=reranker,
    )
    action.current_task = "1"
    resources = action.execute("query").split("\n\n")
    print(resources)
    assert len(resources) == 3
    # test reranked order
    assert resources[0] == "1"
    assert resources[1] == "2"
    assert resources[2] == "0"
