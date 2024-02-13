from unittest.mock import patch

import pytest
from loguru import logger

import sherpa_ai.config as cfg
from sherpa_ai.agents import QAAgent
from sherpa_ai.events import EventType
from sherpa_ai.memory import SharedMemory
from sherpa_ai.models.sherpa_base_chat_model import SherpaChatOpenAI
from sherpa_ai.test_utils.llms import get_llm
from sherpa_ai.tools import SearchTool
from sherpa_ai.utils import extract_numbers_from_text


@pytest.mark.parametrize(
    "test_id, objective, input_data, expected_numbers",
    [
        (
            0,
            "What is the annual salary for an entry level software engineer in Canada?",
            (
                """A software engineer is a person who applies the engineering design process to design, develop, test, maintain, and evaluate computer software.
        The term programmer is sometimes used as a synonym, but may emphasize software implementation over design and can also lack connotations of engineering education or skills.
        the average annual  in Canada is around $9000 to $1,000,170,000 CAD for software engineers""",
                [
                    {
                        "Document": "Description: Entry-Level Software Engineer the average annual  in Canada is around 9,000 to $1,170,000 ",
                        "Source": "https://www.springboard.com/blog/software-engineering/entry-software-engineer-salary/",
                    }
                ],
            ),
            ["9000", "1000170000"],
        ),
        # (
        #     1,
        #     "on june how much cash does Sabio Delivers had?",
        #     (
        #         """Second Quarter 2023 Financial Highlights for Sabio Delivers
        #         Sabio delivered revenues of US$8.0M in Q2-2023, up 11% from US$7.2M in Q2-2022.
        #         CTV/OTT sales as a category increased by 57% to US$5.0 million, compared to US$3.2 million in the prior year's quarter. CTV/OTT sales accounted for 62% of the Company's sales mix, compared with 44% in the prior year's quarter.
        #         Mobile display revenues of US$2.9million in Q2-2023, down 24%, from US$3.9 million in Q2-2022, as our legacy mobile display campaigns continued to shift their spend with Sabio from mobile display to higher-margin mobile OTT streaming, which is recognized under the Company's CTV/OTT revenue category.
        #         Gross Profit of US$4.8 million in Q2-2023, up from US$4.3 million in Q2-2022. Gross Margin improved on a year-over-year basis, from 59% in Q2-2022 to 60% in the completed quarter. The increase is attributable to several efficiency and direct sales improvements within the CTV/OTT channel as well as our App Science business.
        #         Adjusted EBITDA1 loss of US$1.7 million in Q2-2023 compared to a loss of US$1.4 million in Q2-2022. The loss was primarily driven by overhead added during and subsequent to the second quarter of 2022, which included the continued expansion of our sales and marketing apparatus in the prior year and costs associated with transitioning our workforce back to the office. On a sequential basis, second quarter operating expenses, normalized for commissions, were flat in comparison to the first quarter of 2023 as cost efficiencies implemented by management offset incremental headcount additions to our salesforce to position ourselves for the 2024 U.S. elections.
        #         As of June 30, 2023, the Company had cash of US$1.7 million, as compared to US$2.4 million on June 30, 2022.`
        #         As of June 2023, the Company had US$6 million outstanding under its credit facility with Avidbank.""",
        #         [
        #             {
        #                 "Document": "Sabio Delivers 11% Q2-2023 Revenue Growth, Led by 57% Increase in Connected TV/OTT Sales",
        #                 "Source": "https://www.sabioholding.com/press-releases/sabio-delivers-11-q2-2023-revenue-growth-led-by-57-increase-in-connected-tv-ott-sales",
        #             }
        #         ],
        #     ),
        #     ["2.4", "1.4", "30", "2022", "2023", "1.7"],
        # ),
        (
            2,
            "how many players are in a field of a soccer game? and how many referees are there ?",
            (
                """
                Soccer, also known as association football, is a sport played between two teams of 33 players on a rectangular field. The goal is to score more goals than the other team by kicking or heading the ball into the opponent's goal. Players can't use their hands or arms, except for the goalie, to touch the ball. Instead, they can use their legs, head, and torso to pass the ball. Soccer is the world's most popular sport, with 250 million players in over 200 countries. Outside of the United States and Australia, soccer is known as football. The term "soccer" originated in the 1880s when Oxford University students distinguished between "rugger" (rugby football) and "assoccer" (association football). The term was later shortened to 'soccer'.
                """,
                # """Soccer, or football, is a globally adored sport played by two teams of 33 players on a rectangular pitch. The goal is to score more goals than the opposing team by kicking a ball into their net. With over 250 million players in 200+ countries, soccer transcends borders, becoming a universal language of competition and passion. The term "soccer" originated in 19th-century England, distinguishing it from rugby. Today, major tournaments like the FIFA World Cup unite nations and foster cultural pride, highlighting the sport's profound impact on societies worldwide.""",
                # """
                # Association football, commonly referred to as soccer, involves a game between two teams, each comprised of 33 players, on a rectangular field. The primary objective is to outscore the opposing team by propelling the ball into their goal through kicking or heading. Players, excluding the goalie, are restricted from using their hands or arms to handle the ball; instead, they utilize their legs, head, and torso for ball control and passing. Soccer boasts global popularity, with 250 million participants spanning over 200 countries. Beyond the United States and Australia, the sport is recognized as football. The term "soccer" originated in the 1880s when Oxford University students differentiated between 'rugger' (rugby football) and 'assoccer' (association football), eventually evolving into the abbreviated term 'soccer.'
                # """
                [
                    {
                        "Document": "soccer",
                        "Source": "https://www.sabioholding.com/press-releases/sabio-delivers-11-q2-2023-revenue-growth-led-by-57-increase-in-connected-tv-ott-sales",
                    }
                ],
            ),
            ["33", "250", "1880", "200"],
        ),
        (
            3,
            "Who is Tesla's competitor with the second-highest market cap, and what is its market cap? ",
            (
                """
               TSLAOverviewStockScreenerEarningsCalendarSectorsNasdaqSearchTickerSwitchQuote|TSLAU.S.:NasdaqTeslaInc.WATCHLISTALERTNEWSetapricetargetalertOKTSLAUSPREMARKETLastUpdated:Jan4,20247:49a.m.ESTDelayedquote$239.230.780.33%CLOSE$238.45COMPETITORSNAMECHG%MARKETCAPToyotaMotorCorp.1.72%¥35.1TVolkswagenAGNon-VtgPfd.0.67%€58.35BVolkswagenAG0.65%€58.35BMercedes-BenzGroupAG0.42%€67.75BGeneralMotorsCo.-2.16%$49.37BFordMotorCo.-3.70%$48.68BBayerischeMotorenWerkeAG0.63%€64.37BBayerischeMotorenWerkeAGPfd.0.85%€64.37BNIOInc.ADR0.95%$15.01BStellantisN.V.0.20%€66.58BBACKTOTOP
                """,
                [
                    {
                        "Document": "Tesla, Inc. engages in the design, development, manufacture, and sale of fully electric vehicles and energy generation and storage systems. ",
                        "Source": "https://www.marketwatch.com/investing/stock/tsla",
                    }
                ],
            ),
            ["35.1", "58.35", "1880", "200"],
        ),
        (
            4,
            "what is mercury's diameter ?  ",
            (
                """
                Our solar system boasts 8 planets. Mercury, closest to the Sun, faces extreme temperatures. Jupiter, the largest, dazzles with swirling clouds. Pluto, a dwarf planet in the Kuiper Belt. Earth's beauty stands out. Size ranges from Mercury's 3 km diameter to Jupiter's colossal 1,398.22 km. Each planet contributes to the cosmic symphony, revealing the wonders of space.
                """,
                [
                    {
                        "Document": "Our solar system boasts 8 planets. Mercury, closes",
                        "Source": "https://www.chat_gpt.com/investing/stock/tsla",
                    }
                ],
            ),
            ["48.8", "3"],
        ),
        (
            5,
            "how many players are in a field of a soccer game? and how many referees are there ? ",
            (
                """
                One intriguing fact about soccer is that, unlike many other team sports, there are no strict regulations regarding the size or weight of the soccer ball. According to the Laws of the Game set by the International Football Association Board (IFAB), a soccer ball should have a circumference of 68-70 cm (27-28 inches) and a weight of 410-450 grams (14-16 ounces).
                In terms of the number of players, a standard soccer match is played with 16.5 players on each team, including one goalkeeper. This configuration has been widely adopted globally, contributing to the sport's balance of strategy, teamwork, and individual skill. The dynamic interplay of 33 players on .
                """,
                # """Soccer, or football, is a globally adored sport played by two teams of 33 players on a rectangular pitch. The goal is to score more goals than the opposing team by kicking a ball into their net. With over 250 million players in 200+ countries, soccer transcends borders, becoming a universal language of competition and passion. The term "soccer" originated in 19th-century England, distinguishing it from rugby. Today, major tournaments like the FIFA World Cup unite nations and foster cultural pride, highlighting the sport's profound impact on societies worldwide.""",
                [
                    {
                        "Document": "soccer",
                        "Source": "https://www.sabioholding.com/press-releases/sabio-delivers-11-q2-2023-revenue-growth-led-by-57-increase-in-connected-tv-ott-sales",
                    }
                ],
            ),
            ["33", "16.5"],
        ),
        (
            6,
            "what is unique about ethiopian callender? and Please provide the answer in numerical form.",
            (
                """
                One intriguing fact about soccer is that, unlike many other team sports, there are no strict regulations regarding the size or weight of the soccer ball. According to the Laws of the Game set by the International Football Association Board (IFAB), a soccer ball should have a circumference of 68-70 cm (27-28 inches) and a weight of 410-450 grams (14-16 ounces).
                In terms of the number of players, a standard soccer match is played with 16.5 players on each team, including one goalkeeper. This configuration has been widely adopted globally, contributing to the sport's balance of strategy, teamwork, and individual skill. The dynamic interplay of 33 players on .
                """,
                # """Soccer, or football, is a globally adored sport played by two teams of 33 players on a rectangular pitch. The goal is to score more goals than the opposing team by kicking a ball into their net. With over 250 million players in 200+ countries, soccer transcends borders, becoming a universal language of competition and passion. The term "soccer" originated in 19th-century England, distinguishing it from rugby. Today, major tournaments like the FIFA World Cup unite nations and foster cultural pride, highlighting the sport's profound impact on societies worldwide.""",
                [
                    {
                        "Document": "soccer",
                        "Source": "https://www.sabioholding.com/press-releases/sabio-delivers-11-q2-2023-revenue-growth-led-by-57-increase-in-connected-tv-ott-sales",
                    }
                ],
            ),
            [],
        ),
        #  (
        #     "what is unique about ethiopian callender? and Please provide the answer in numerical form.",
        #     (
        #         """
        #         Ehtiopia has thirteen months.""",
        #         [
        #             {
        #                 "Document": "soccer",
        #                 "Source": "https://www.sabioholding.com/press-releases/sabio-delivers-11-q2-2023-revenue-growth-led-by-57-increase-in-connected-tv-ott-sales",
        #             }
        #         ],
        #     ),
        #     []
        # ),
    ],
)
def test_number_citation_succeeds_in_qa(
    get_llm, test_id, input_data, expected_numbers, objective
):  # noqa: F811
    llm = get_llm(
        __file__, test_number_citation_succeeds_in_qa.__name__ + f"_{str(test_id)}"
    )

    data = input_data[0]

    shared_memory = SharedMemory(
        objective=objective,
        agent_pool=None,
    )
    with patch.object(SearchTool, "_run", return_value=data):
        task_agent = QAAgent(
            llm=llm,
            shared_memory=shared_memory,
            require_meta=False,
            num_runs=1,
            perform_number_validation=True,
        )

        shared_memory.add(
            EventType.task,
            "Planner",
            objective,
        )

        task_agent.run()

        results = shared_memory.get_by_type(EventType.result)
        data_numbers = expected_numbers
        logger.debug(results[0].content)
        for number in extract_numbers_from_text(results[0].content):
            if number in data_numbers or len(data_numbers) == 0:
                pass
            else:
                assert False, number + " was not found in resource"

        assert True
