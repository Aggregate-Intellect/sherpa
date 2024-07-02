from unittest.mock import MagicMock, patch

import pytest

from sherpa_ai.actions.google_search import GoogleSearch
from sherpa_ai.actions.utils.reranking import RerankingByQuery


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


def embedding_query(text):
    return_values = [[1, 0, 0], [1, 1, 1], [1, 1, 0]]
    return return_values[int(text)]


def embedding_documents(texts):
    results = []
    for text in texts:
        results.append(embedding_query(text))

    return results


@pytest.fixture
def mock_embeddings():
    embeddings = MagicMock()
    embeddings.embed_query.side_effect = embedding_query
    embeddings.embed_documents.side_effect = embedding_documents

    return embeddings


def test_default_reranker(mock_google_search, mock_embeddings):
    reranker = RerankingByQuery(embeddings=mock_embeddings)

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
