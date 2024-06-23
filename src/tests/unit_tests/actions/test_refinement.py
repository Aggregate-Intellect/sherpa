from unittest.mock import MagicMock, patch

import pytest

from sherpa_ai.actions.utils.refinement import RefinementByQuery
from sherpa_ai.test_utils.llms import get_llm

documents= [ "Come on down to the event and show your support for small businesses and entrepreneurs in Toronto. It’s sure to be an amazing time, with something for everyone! We can’t wait to see you there.This is a great opportunity to buy unique locally made items while supporting the local economy. You’ll find some truly one-of-a-kind pieces from talented artisans, perfect for gifts or just to treat yourself.Follow us on Instagram (@queenstreetmarketplac) for updates and more information about the Queen St Marketplace. We look forward to seeing you all this weekend at Trinity Bellwoods Park.", 
            "One of my favorite places to shop in Toronto. PERFECT for gifts and home decor, jewelry, candles, etc! Always a great find. Everything is sourced/ made by local artists.The owner Dan cares about each and every artist and is very customer service oriented.A very fun place to shop and hangout.Check out their other two locations.",
            "SoBEACHES ARTISAN MARKET 2075 Queen East Bring your family and friends to Queen St Marketplace for a day of shopping and fun.  Admission is free for everyone, kids get an extra treat with free face painting. Enjoy the handcrafted works of over 50 independent artists, artisans, makers, and designers, while your little ones are transformed into their favorite characters."
            ]

query="Why summer market is popular in Toronto?"



def test_default_reranker(get_llm):
    llm = get_llm(__file__, test_default_reranker.__name__)

    rfiner= RefinementByQuery(llm=llm)
    output_refined=rfiner.refinement(documents,query)
    #test if output have <3 sentences (k=3, k is the max number of sentences after refinement)
    assert max([doc.count(".") for doc in output_refined])<=3
   