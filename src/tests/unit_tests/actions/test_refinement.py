from unittest.mock import MagicMock, patch

import pytest
from loguru import logger

from sherpa_ai.actions.utils.refinement import RefinementByQuery
from sherpa_ai.test_utils.llms import get_llm


documents = [
    "Come on down to the event and show your support for small businesses and entrepreneurs in Toronto. It’s sure to be an amazing time, with something for everyone! We can’t wait to see you there.This is a great opportunity to buy unique locally made items while supporting the local economy. You’ll find some truly one-of-a-kind pieces from talented artisans, perfect for gifts or just to treat yourself.Follow us on Instagram (@queenstreetmarketplac) for updates and more information about the Queen St Marketplace. We look forward to seeing you all this weekend at Trinity Bellwoods Park.",
    "One of my favorite places to shop in Toronto. PERFECT for gifts and home decor, jewelry, candles, etc! Always a great find. Everything is sourced/ made by local artists.The owner Dan cares about each and every artist and is very customer service oriented.A very fun place to shop and hangout.Check out their other two locations.",
    "SoBEACHES ARTISAN MARKET 2075 Queen East Bring your family and friends to Queen St Marketplace for a day of shopping and fun.  Admission is free for everyone, kids get an extra treat with free face painting. Enjoy the handcrafted works of over 50 independent artists, artisans, makers, and designers, while your little ones are transformed into their favorite characters.",
]

query = "Why summer market is popular in Toronto?"

documents_not_related = [
    "Iron Man fears Hulk more than anybody.",
    "Hulk was named the strongest Avenger on Sakaar.",
    "Natasha loves Bruce Banner.",
    "SHIELD built a contingency plan only for Hulk if he gets angry.",
]

query_not_related = "Why is Hulk the strongest Avenger?"


def test_default_refinement(get_llm):
    llm = get_llm(__file__, test_default_refinement.__name__)

    rfiner = RefinementByQuery(llm=llm)
    output_refined = rfiner.refinement(documents, query)
    logger.info(output_refined)
    # test if output have <3 sentences (k=3, k is the max number of sentences after refinement)
    assert max([doc.count(".") for doc in output_refined]) <= 3
    assert len(output_refined) == 3


def test_refinement_not_question(get_llm):
    query = "Best summer market in Toronto"
    llm = get_llm(__file__, test_refinement_not_question.__name__)

    rfiner = RefinementByQuery(llm=llm)
    output_refined = rfiner.refinement(documents, query)
    logger.info(output_refined)
    # test if output have <3 sentences (k=3, k is the max number of sentences after refinement)
    assert max([doc.count(".") for doc in output_refined]) <= 3
    assert len(output_refined) == 3


def test_default_refinement_not_related(get_llm):
    llm = get_llm(__file__, test_default_refinement_not_related.__name__)

    rfiner = RefinementByQuery(llm=llm)
    output_refined = rfiner.refinement(documents_not_related, query_not_related)

    # test if output have <3 sentences (k=3, k is the max number of sentences after refinement)
    assert max([doc.count(".") for doc in output_refined]) <= 3
    assert len(output_refined) == 3
