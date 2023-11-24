import pytest

from sherpa_ai.actions.context_search import ContextSearch
from tests.fixtures.llms import get_llm


@pytest.mark.external_api
def test_context_search_succeeds(get_llm):  # noqa: F811
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
