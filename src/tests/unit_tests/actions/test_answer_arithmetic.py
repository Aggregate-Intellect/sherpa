from sherpa_ai.actions import AnswerArithmetic


def test_answer_arith():
    m = AnswerArithmetic(placeholder=False)
    question = (
        "if each apple costs 2 dollar. How much money do I need for buying 10 apples?"
    )
    answer = 20
    result = m.execute(question)

    assert answer == result


def test_answer_arith_placeholder():
    m = AnswerArithmetic(placeholder=True)
    question = (
        "if each apple costs 2 dollar. How much money do I need for buying 10 apples?"
    )
    answer = 20
    result = m.execute(question)

    assert answer == result
