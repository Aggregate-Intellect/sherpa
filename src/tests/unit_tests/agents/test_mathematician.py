from sherpa_ai.agents import Mathematician


def test_answer_arith():
    m = Mathematician(llm=None)
    question = (
        "if each apple costs 2 dollar. How much money do I need for buying 10 apples?"
    )

    answer = 20
    result = m.answer_arithmetic(question)

    assert answer == result

    result = m.answer_arithmetic(question, True)

    assert answer == result
