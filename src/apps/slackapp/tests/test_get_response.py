from datetime import datetime

import pytest
from slackapp.bolt_app import get_response

import sherpa_ai.config as cfg
from sherpa_ai.verbose_loggers import DummyVerboseLogger


@pytest.mark.real
def test_get_response_contains_todays_date():
    question = "What is the date today, using the following format: YYYY-MM-DD?"
    date = datetime.now().strftime("%Y-%m-%d")

    if cfg.SERPER_API_KEY is None:
        pytest.skip(
            "SERPER_API_KEY not found in environment variables, skipping this test"
        )

    verbose_logger = DummyVerboseLogger()

    response = get_response(
        question=question,
        previous_messages=[],
        user_id="",
        team_id="",
        verbose_logger=verbose_logger,
        bot_info={"user_id": "Sherpa"},
    )
    assert date in response, "Today's date not found in response"


@pytest.mark.real
def test_response_contains_correct_info():
    question = "What is AutoGPT and how does it compare with MetaGPT"

    if cfg.SERPER_API_KEY is None:
        pytest.skip(
            "SERPER_API_KEY not found in environment variables, skipping this test"
        )

    verbose_logger = DummyVerboseLogger()

    response = get_response(
        question=question,
        previous_messages=[],
        user_id="",
        team_id="",
        verbose_logger=verbose_logger,
        bot_info={"user_id": "Sherpa"},
    )

    print(response)
    assert response is not None
    assert response != ""
    assert "AutoGPT" in response
    assert "MetaGPT" in response
