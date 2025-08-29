from unittest import mock

import pytest

from sherpa_ai.test_utils.llms import get_llm


def _is_chroma_available():
    """Check if langchain_chroma is available."""
    try:
        import langchain_chroma
        return True
    except ImportError:
        return False


# Only import ContextSearch if langchain_chroma is available
if _is_chroma_available():
    from sherpa_ai.actions.context_search import ContextSearch


@pytest.fixture
def mock_context_search(external_api):
    # Always mock VectorStoreRetriever to simulate the vector database
    with mock.patch(
        "langchain_core.vectorstores.VectorStoreRetriever.get_relevant_documents"
    ) as mock_retrival:
        mock_doc = mock.MagicMock()
        mock_doc.page_content = "mock"
        mock_doc.metadata = {"source": "mock"}

        mock_retrival.return_value = [mock_doc]
        yield


@pytest.mark.skipif(not _is_chroma_available(), reason="langchain_chroma not available")
def test_context_search_succeeds(get_llm, mock_context_search):  # noqa: F811
    role_description = (
        "The programmer receives requirements about a program and write it"
    )

    task = """We need to render a highly complex 3D image on the solar system. We can use any publicly avaliable
    resources to achieve this task."""  # noqa: E501

    llm = get_llm(__file__, test_context_search_succeeds.__name__)

    context_search = ContextSearch(
        role_description=role_description, task=task, llm=llm
    )

    result = context_search.execute(task)

    assert len(result) > 0
    assert len(context_search.resources) > 0
    assert context_search.resources[0].source == "mock"
