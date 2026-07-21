"""Behavior tests for the Sherpa langchain model wrappers.

These wrappers subclass langchain base classes directly, so they are the
first thing to break when langchain changes its model APIs. The tests below
verify real generation behavior (not just construction) using langchain's
fake chat models.
"""

import json
from unittest import mock

import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from loguru import logger as loguru_logger

from sherpa_ai.models.chat_model_with_logging import ChatModelWithLogging
from sherpa_ai.models.sherpa_base_chat_model import (
    SherpaBaseChatModel,
    SherpaChatOpenAI,
)


class FakeSherpaChatModel(SherpaBaseChatModel, FakeListChatModel):
    """SherpaBaseChatModel backed by canned responses for testing."""


def test_chat_model_with_logging_generates_and_logs():
    inner = FakeListChatModel(responses=["logged response"])
    records = []
    handler_id = loguru_logger.add(
        lambda message: records.append(message), format="{message}", level="INFO"
    )
    try:
        model = ChatModelWithLogging(llm=inner, logger=loguru_logger)
        result = model.invoke([HumanMessage(content="hello\nworld")])
    finally:
        loguru_logger.remove(handler_id)

    # The wrapped model's response must flow through unchanged
    assert isinstance(result, AIMessage)
    assert result.content == "logged response"

    # Exactly one structured log entry with the input/output/llm name
    assert len(records) == 1
    log = json.loads(str(records[0]))
    assert log["output"] == "logged response"
    assert log["input"] == [{"text": "hello\\nworld", "agent": "human"}]
    assert log["llm_name"] == inner._llm_type


def test_sherpa_base_chat_model_returns_result_without_user_id():
    model = FakeSherpaChatModel(responses=["fake answer"])

    result = model.invoke([HumanMessage(content="question")])

    assert result.content == "fake answer"


def test_sherpa_base_chat_model_tracks_usage_for_user():
    model = FakeSherpaChatModel(responses=["tracked answer"], user_id="user-42")

    with mock.patch(
        "sherpa_ai.models.sherpa_base_chat_model.UserUsageTracker"
    ) as mock_tracker:
        result = model.invoke([HumanMessage(content="question")])

    assert result.content == "tracked answer"
    # Usage must be recorded exactly once for the user and the DB closed
    mock_tracker.return_value.add_usage.assert_called_once()
    assert (
        mock_tracker.return_value.add_usage.call_args.kwargs["user_id"] == "user-42"
    )
    mock_tracker.return_value.close_connection.assert_called_once()


def test_sherpa_base_chat_model_tracks_usage_from_populated_metadata():
    # The two tests above only exercise the fallback path (no usage_metadata
    # on the message). This covers the actual extraction path: when the
    # generated message carries real usage_metadata, it must be read and
    # passed through to add_usage verbatim, not the zeroed-out fallback.
    model = FakeSherpaChatModel(responses=["tracked answer"], user_id="user-99")

    usage_metadata = {"input_tokens": 12, "output_tokens": 34, "total_tokens": 46}
    canned = ChatResult(
        generations=[
            ChatGeneration(
                message=AIMessage(
                    content="tracked answer", usage_metadata=usage_metadata
                )
            )
        ]
    )

    with mock.patch(
        "langchain_core.language_models.fake_chat_models.FakeListChatModel._generate",
        return_value=canned,
    ), mock.patch(
        "sherpa_ai.models.sherpa_base_chat_model.UserUsageTracker"
    ) as mock_tracker:
        model.invoke([HumanMessage(content="question")])

    mock_tracker.return_value.add_usage.assert_called_once()
    assert (
        mock_tracker.return_value.add_usage.call_args.kwargs["usage_metadata"]
        == usage_metadata
    )
    # The fallback (zeroed) path must NOT be used when real metadata exists.
    assert "input_tokens" not in mock_tracker.return_value.add_usage.call_args.kwargs


def test_sherpa_chat_openai_construction_and_fields():
    # Subclassing ChatOpenAI must keep working: pydantic fields from both the
    # parent (model_name, temperature) and the Sherpa extension must coexist.
    model = SherpaChatOpenAI(
        model_name="gpt-4o-mini",
        temperature=0,
        openai_api_key="dummy",
        user_id="user-1",
        session_id="session-1",
        agent_name="agent-1",
    )

    assert model.model_name == "gpt-4o-mini"
    assert model.user_id == "user-1"
    assert model.session_id == "session-1"
    assert model.agent_name == "agent-1"


def test_sherpa_chat_openai_generate_tracks_usage():
    model = SherpaChatOpenAI(
        model_name="gpt-4o-mini",
        temperature=0,
        openai_api_key="dummy",
        user_id="user-7",
    )

    canned = ChatResult(
        generations=[ChatGeneration(message=AIMessage(content="openai answer"))]
    )

    # Patch the parent class generation so no network call happens, while the
    # Sherpa override (usage tracking) still runs for real.
    with mock.patch(
        "sherpa_ai.models.sherpa_base_chat_model.ChatOpenAI._generate",
        return_value=canned,
    ), mock.patch(
        "sherpa_ai.models.sherpa_base_chat_model.UserUsageTracker"
    ) as mock_tracker:
        result = model._generate([HumanMessage(content="question")])

    assert result.generations[0].message.content == "openai answer"
    mock_tracker.return_value.add_usage.assert_called_once()
    assert mock_tracker.return_value.add_usage.call_args.kwargs["user_id"] == "user-7"
    assert (
        mock_tracker.return_value.add_usage.call_args.kwargs["model_name"]
        == "gpt-4o-mini"
    )
