import pytest

from sherpa_ai.actions import AnswerArithmetic
from sherpa_ai.test_utils.llms import get_llm


@pytest.mark.external_api
def test_answer_arith(get_llm):
    llm = get_llm(__file__, test_answer_arith.__name__)
    m = AnswerArithmetic(placeholder=False)
    question = (
        "if each apple costs 2 dollar. How much money do I need for buying 10 apples?"
    )
    answer = 20
    result = m.execute(question)

    assert answer == result


@pytest.mark.external_api
def test_answer_arith_placeholder(get_llm):
    llm = get_llm(__file__, test_answer_arith_placeholder.__name__)

    m = AnswerArithmetic(placeholder=True)
    question = (
        "if each apple costs 2 dollar. How much money do I need for buying 10 apples?"
    )
    answer = 20
    result = m.execute(question)

    assert answer == result
