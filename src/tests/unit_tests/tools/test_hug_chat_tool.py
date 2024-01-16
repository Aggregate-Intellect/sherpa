import unittest
from unittest.mock import MagicMock, patch

import pytest
from hugchat import hugchat

import sherpa_ai.config as cfg
from sherpa_ai.tools import HugChatTool


class FakeCookies:
    def get_dict(self):
        return {}


class FakeLogin:
    def __init__(self, email: str, passwd: str = "") -> None:
        pass

    def login(self):
        return FakeCookies()


class FakeChatBot:
    def __init__(self, cookies=None):
        pass

    def query(self, query, stream=False, web_search=False):
        return MagicMock(text="Fake response")


class TestHugChatTool(unittest.TestCase):
    def test_not_authenticated_after_initialization(self):
        tool = HugChatTool()
        assert not tool.authenticated()

    def test_authenticated_after_login(self):
        with patch("sherpa_ai.tools.Login", FakeLogin):
            tool = HugChatTool(username="user@foo.com", password="blah")
            tool.login()
            assert tool.authenticated()

    def test_login_fails_without_username(self):
        with patch("sherpa_ai.tools.Login", FakeLogin):
            tool = HugChatTool(username=None, password="blah")
            assert tool.login() is None

    def test_login_fails_without_password(self):
        with patch("sherpa_ai.tools.Login", FakeLogin):
            tool = HugChatTool(username="some@one.com", password="")
            assert tool.login() is None

    def test_stream_option_defaults_to_false(self):
        tool = HugChatTool(username="some@one.com", password="")
        assert tool.stream_results is False

    def test_web_search_option_defaults_to_false(self):
        tool = HugChatTool(username="some@one.com", password="")
        assert tool.web_search is False

    def test_options_can_be_specified(self):
        tool = HugChatTool(
            username="some@one.com", password="", stream_results=True, web_search=True
        )
        assert tool.stream_results
        assert tool.web_search

    def test_run_returns_none_when_unauthenticated(self):
        with patch(
            "sherpa_ai.tools.HugChatTool.authenticated", return_value=False
        ), patch("sherpa_ai.tools.Login", FakeLogin):
            tool = HugChatTool(username="user@foo.com", password="blah")
            response = tool.run("doesn't matter")
            assert response is None

    def test_run_returns_mock_query_returns_response_when_authenticated(self):
        with patch(
            "sherpa_ai.tools.HugChatTool.authenticated", return_value=True
        ), patch("sherpa_ai.tools.Login", FakeLogin), patch(
            "sherpa_ai.tools.ChatBot", FakeChatBot
        ):
            tool = HugChatTool(username="user@foo.com", password="blah")
            question = "What is langchain?"
            response = tool.run(question)
            assert "fake response" in response.text.lower(), "unexpected response"

    @pytest.mark.external_api
    def test_run_returns_real_query_response_when_authenticated(self):
        if cfg.HUGCHAT_EMAIL is not None and cfg.HUGCHAT_PASS is not None:
            tool = HugChatTool(username=cfg.HUGCHAT_EMAIL, password=cfg.HUGCHAT_PASS)
            question = "What is langchain?"
            response = tool.run(question)
            assert (
                "langchain" in response.text.lower()
            ), "langchain not found in response"
        else:
            pytest.skip("HUGCHAT username and password not set in environment")

    def test_async_run_is_not_supported(self):
        tool = HugChatTool(username="user@foo.com", password="blah")
        with self.assertRaises(NotImplementedError):
            tool._arun("some query")
