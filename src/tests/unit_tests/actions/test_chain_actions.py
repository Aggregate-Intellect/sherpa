from unittest.mock import MagicMock, patch

import pytest
from loguru import logger
from nltk import tokenize

from sherpa_ai.actions import arxiv_search, dynamic, empty
from sherpa_ai.actions.chain_actions import ChainActions
from sherpa_ai.test_utils.llms import get_llm


def test_specific_chain_actions():
    def test_sum(num_1: int, num_2: int):
        return num_1 + num_2

    def test_root(num):
        return num**0.5

    action_1 = dynamic.DynamicAction(
        action=test_sum,
        name="test_sum",
        args={"num_1": "int", "num_2": "int"},
        usage="for test",
    )
    action_2 = empty.EmptyAction()
    action_3 = dynamic.DynamicAction(
        action=test_root, name="test_root", args={"num": "int"}, usage="for test"
    )

    actions_list = [action_1, action_2, action_3]
    instruction = [{}, {}, {"num": {"action": 1, "output": 0}}]

    chainActions = ChainActions(
        actions=actions_list,
        instruction=instruction,
        name="chain_actions",
        args={"num_1": "int", "num_2": "int"},
        usage="for test",
    )
    res = chainActions(num_1=3, num_2=6)
    # test if output have <3 sentences (k=3, k is the max number of sentences after refinement)
    assert res == 3
