import sys
from unittest import mock

import pytest

from sherpa_ai.actions import AnswerArithmetic


@pytest.fixture
def mock_code_snippet(external_api):
    if external_api:
        return

    function = "def solution():\n    return 2 * 10"

    with mock.patch("pal.core.interface.ProgramInterface.generate") as mock_retrival:
        mock_retrival.return_value = [function.split("\n")]
        yield


@pytest.fixture
def mock_code_snippet_placeholder(external_api):
    if external_api:
        return

    function = "def solution():\n    return number_1 * number_2"

    with mock.patch("pal.core.interface.ProgramInterface.generate") as mock_retrival:
        mock_retrival.return_value = [function.split("\n")]
        yield


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="The Pal package used in arithmetic action is not supported on Windows.",
)
@pytest.mark.external_api
def test_answer_arith(mock_code_snippet):
    m = AnswerArithmetic(placeholder=False)
    question = (
        "if each apple costs 2 dollar. How much money do I need for buying 10 apples?"
    )
    answer = 20
    result = m.execute(question)

    assert answer == result


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="The Pal package used in arithmetic action is not supported on Windows.",
)
@pytest.mark.external_api
def test_answer_arith_placeholder(mock_code_snippet_placeholder):
    m = AnswerArithmetic(placeholder=True)
    question = (
        "if each apple costs 2 dollar. How much money do I need for buying 10 apples?"
    )
    answer = 20
    result = m.execute(question)

    assert answer == result
