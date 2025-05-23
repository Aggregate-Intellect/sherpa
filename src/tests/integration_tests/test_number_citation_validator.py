from unittest.mock import patch

import pytest
from loguru import logger

import sherpa_ai.config as cfg
from sherpa_ai.agents import QAAgent
from sherpa_ai.memory import SharedMemory
from sherpa_ai.models.sherpa_base_chat_model import SherpaChatOpenAI
from sherpa_ai.output_parsers.number_validation import NumberValidation
from sherpa_ai.test_utils.llms import get_llm
from sherpa_ai.tools import SearchTool
from sherpa_ai.utils import combined_number_extractor


@pytest.mark.parametrize(
    "test_id, objective, input_data, expected_numbers",
    [
        (
            1,
            "on june how much cash does Sabio Delivers had?",
            [
                {
                    "Document": """Second Quarter 2023 Financial Highlights for Sabio Delivers
                    Sabio delivered revenues of US$8.0M in Q2-2023, up 11% from US$7.2M in Q2-2022.
                    CTV/OTT sales as a category increased by 57% to US$5.0 million, compared to US$3.2 million in the prior year's quarter. CTV/OTT sales accounted for 62% of the Company's sales mix, compared with 44% in the prior year's quarter.
                    Mobile display revenues of US$2.9million in Q2-2023, down 24%, from US$3.9 million in Q2-2022, as our legacy mobile display campaigns continued to shift their spend with Sabio from mobile display to higher-margin mobile OTT streaming, which is recognized under the Company's CTV/OTT revenue category.
                    Gross Profit of US$4.8 million in Q2-2023, up from US$4.3 million in Q2-2022. Gross Margin improved on a year-over-year basis, from 59% in Q2-2022 to 60% in the completed quarter. The increase is attributable to several efficiency and direct sales improvements within the CTV/OTT channel as well as our App Science business.
                    Adjusted EBITDA1 loss of US$1.7 million in Q2-2023 compared to a loss of US$1.4 million in Q2-2022. The loss was primarily driven by overhead added during and subsequent to the second quarter of 2022, which included the continued expansion of our sales and marketing apparatus in the prior year and costs associated with transitioning our workforce back to the office. On a sequential basis, second quarter operating expenses, normalized for commissions, were flat in comparison to the first quarter of 2023 as cost efficiencies implemented by management offset incremental headcount additions to our salesforce to position ourselves for the 2024 U.S. elections.
                    As of June 30, 2023, the Company had cash of US$1.7 million, as compared to US$2.4 million on June 30, 2022.`
                    As of June 2023, the Company had US$6 million outstanding under its credit facility with Avidbank.""",
                    "Source": "https://www.sabioholding.com/press-releases/sabio-delivers-11-q2-2023-revenue-growth-led-by-57-increase-in-connected-tv-ott-sales",
                }
            ],
            ["1.7"],
        ),
        (
            2,
            "how many players are in a field of a soccer game? ",
            [
                {
                    "Document": "Soccer, also known as association football, is a sport played between two teams of 33 players on a rectangular field. The goal is to score more goals than the other team by kicking or heading the ball into the opponent's goal. Players can't use their hands or arms, except for the goalie, to touch the ball. Instead, they can use their legs, head, and torso to pass the ball. Soccer is the world's most popular sport, with 250 million players in over 200 countries. Outside of the United States and Australia, soccer is known as football. The term 'soccer' originated in the 1880s when Oxford University students distinguished between 'rugger' (rugby football) and 'assoccer' (association football). The term was later shortened to 'soccer'.",
                    "Source": "https://www.sabioholding.com/press-releases/sabio-delivers-11-q2-2023-revenue-growth-led-by-57-increase-in-connected-tv-ott-sales",
                }
            ],
            ["33"],
        ),
        (
            3,
            "Who is Tesla's competitor with the second-highest market cap, and what is its market cap? ",
            [
                {
                    "Document": "TSLAOverviewStockScreenerEarningsCalendarSectorsNasdaqSearchTickerSwitchQuote|TSLAU.S.:NasdaqTeslaInc.WATCHLISTALERTNEWSetapricetargetalertOKTSLAUSPREMARKETLastUpdated:Jan4,20247:49a.m.ESTDelayedquote$239.230.780.33%CLOSE$238.45COMPETITORSNAMECHG%MARKETCAPToyotaMotorCorp.1.72%¥35.1TVolkswagenAGNon-VtgPfd.0.67%€58.35BVolkswagenAG0.65%€58.35BMercedes-BenzGroupAG0.42%€67.75BGeneralMotorsCo.-2.16%$49.37BFordMotorCo.-3.70%$48.68BBayerischeMotorenWerkeAG0.63%€64.37BBayerischeMotorenWerkeAGPfd.0.85%€64.37BNIOInc.ADR0.95%$15.01BStellantisN.V.0.20%€66.58BBACKTOTOP",
                    "Source": "https://www.marketwatch.com/investing/stock/tsla",
                }
            ],
            ["35.1"],
        ),
        (
            4,
            "what is mercury's diameter ?  ",
            [
                {
                    "Document": "Our solar system boasts 8 planets. Mercury, closest to the Sun, faces extreme temperatures. Jupiter, the largest, dazzles with swirling clouds. Pluto, a dwarf planet in the Kuiper Belt. Earth's beauty stands out. Size ranges from Mercury's 3 km diameter to Jupiter's colossal 1,398.22 km. Each planet contributes to the cosmic symphony, revealing the wonders of space.",
                    "Source": "https://www.chat_gpt.com/investing/stock/tsla",
                }
            ],
            ["3"],
        ),
        (
            5,
            "how many players are in a field of a soccer game? and how many referees are there ? ",
            [
                {
                    "Document": "intriguing fact about soccer is that, unlike many other team sports, there are no strict regulations regarding the size or weight of the soccer ball. According to the Laws of the Game set by the International Football Association Board (IFAB), a soccer ball should have a circumference of 68-70 cm (27-28 inches) and a weight of 410-450 grams (14-16 ounces). In terms of the number of players, a standard soccer match is played with 16.5 players on each team, including one goalkeeper. This configuration has been widely adopted globally, contributing to the sport's balance of strategy, teamwork, and individual skill. The dynamic interplay of 33 players on .",
                    "Source": "https://www.sabioholding.com/press-releases/sabio-delivers-11-q2-2023-revenue-growth-led-by-57-increase-in-connected-tv-ott-sales",
                }
            ],
            ["33", "16.5"],
        ),
        (
            6,
            "what is unique about ethiopian callender? and Please provide the answer in numerical form.",
            [
                {
                    "Document": "Ehtiopia has thirteen months.",
                    "Source": "https://www.sabioholding.com/press-releases/sabio-delivers-11-q2-2023-revenue-growth-led-by-57-increase-in-connected-tv-ott-sales",
                }
            ],
            ["13"],
        ),
        (
            7,
            "what are the numbers mentioned in the context",
            [
                {
                    "Document": "One Thousand Two Hundred Thirty-Four feet are also  567 and there are 56.45 others 123,345",
                    "Source": "https://www.sabioholding.com/press-releases/sabio-delivers-11-q2-2023-revenue-growth-led-by-57-increase-in-connected-tv-ott-sales",
                }
            ],
            ["1234", "567", "56.45", "123345"],
        ),
        (
            8,
            "how many dogs are going to be in the rally GGH?",
            [
                {
                    "Document": "In the rally GGH there are going to be One Thousand Two Hundred Thirty-Four dogs. and also one thousand cats.  there are going to be also event for wolves and lions.",
                    "Source": "https://www.sabioholding.com/press-releases/sabio-delivers-11-q2-2023-revenue-growth-led-by-57-increase-in-connected-tv-ott-sales",
                }
            ],
            ["1234"],
        ),
    ],
)
def test_number_citation_succeeds_in_qa(
    get_llm, test_id, input_data, expected_numbers, objective  # noqa: F811
):
    llm = get_llm(
        __file__, test_number_citation_succeeds_in_qa.__name__ + f"_{str(test_id)}"
    )
    data = input_data

    shared_memory = SharedMemory(
        objective=objective,
    )
    number_validation = NumberValidation()
    with patch.object(SearchTool, "_run", return_value=data):
        task_agent = QAAgent(
            llm=llm,
            shared_memory=shared_memory,
            num_runs=1,
            validations=[number_validation],
            validation_steps=3,
        )

        shared_memory.add(
            "task",
            "Planner",
            content=objective,
        )
        event = shared_memory.events[-1]
        task_agent.belief.current_task = event
        task_agent.belief.internal_events = [event]
        task_agent.belief.events = [event]

        task_agent.run()

        results = shared_memory.get_by_type("result")
        data_numbers = expected_numbers

        logger.debug(results[0].content)
        for number in data_numbers:
            assert number in combined_number_extractor(results[0].content), (
                number + " was not found in resource"
            )
        assert True
