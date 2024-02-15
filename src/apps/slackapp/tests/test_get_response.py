from datetime import datetime
from unittest.mock import MagicMock

import pytest
from langchain.llms.fake import FakeListLLM
from loguru import logger
from slackapp.bolt_app import get_response

import sherpa_ai.config as cfg
from sherpa_ai.test_utils.llms import get_llm
from sherpa_ai.verbose_loggers import DummyVerboseLogger
from tests.conftest import external_api


@pytest.mark.external_api
def test_get_response_contains_todays_date(get_llm):  # noqa: F811
    llm = get_llm(__file__, test_get_response_contains_todays_date.__name__)

    question = "What is the date today, using the following format: YYYY-MM-DD?"
    date = (
        llm.responses[-1]
        if isinstance(llm, FakeListLLM)
        else datetime.now().strftime("%Y-%m-%d")
    )

    verbose_logger = DummyVerboseLogger()

    response = get_response(
        question=question,
        previous_messages=[],
        verbose_logger=verbose_logger,
        bot_info={"user_id": "Sherpa"},
        llm=llm,
    )
    assert date in response, "Today's date not found in response"


@pytest.mark.external_api
def test_response_is_verbose_by_default(get_llm):  # noqa: F811
    if cfg.SERPER_API_KEY is None:
        pytest.skip(
            "SERPER_API_KEY not found in environment variables, skipping this test"
        )

    llm = get_llm(__file__, test_response_is_verbose_by_default.__name__)
    question = "What is AutoGPT and how does it compare with MetaGPT"

    verbose_logger = MagicMock()
    verbose_logger.log = MagicMock()
    response = get_response(
        question=question,
        previous_messages=[],
        verbose_logger=verbose_logger,
        bot_info={"user_id": "Sherpa"},
        llm=llm,
    )
    logger.info(response)
    verbose_logger.log.assert_called()

    assert response is not None
    assert response != ""
    assert "AutoGPT" in response
    assert "MetaGPT" in response


@pytest.mark.external_api
def test_response_concise_is_not_verbose(get_llm):  # noqa: F811
    if cfg.SERPER_API_KEY is None:
        pytest.skip(
            "SERPER_API_KEY not found in environment variables, skipping this test"
        )
    llm = get_llm(__file__, test_response_concise_is_not_verbose.__name__)
    question = "What is AutoGPT and how does it compare with MetaGPT --concise"

    verbose_logger = MagicMock()
    verbose_logger.log = MagicMock()
    response = get_response(
        question=question,
        previous_messages=[],
        verbose_logger=verbose_logger,
        bot_info={"user_id": "Sherpa"},
        llm=llm,
    )
    logger.info(response)
    verbose_logger.log.assert_not_called()

    assert response is not None
    assert response != ""
    assert "AutoGPT" in response
    assert "MetaGPT" in response
