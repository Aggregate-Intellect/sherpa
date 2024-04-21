from unittest.mock import mock_open, patch

import pytest
from flask import Flask

from slackapp import rollbar_support
from slackapp.rollbar_support import ROLLBAR_IMPORTED, enable_rollbar


@pytest.mark.skipif(
    not ROLLBAR_IMPORTED, reason="rollbar not installed via poetry --extras"
)
@patch("slackapp.rollbar_support.rollbar.init", autospec=True)
class TestEnableRollbar:
    @pytest.fixture()
    def mock_app(self):
        app = Flask(__name__)
        app.config["TESTING"] = True
        yield app

    @patch.object(rollbar_support.cfg, "ROLLBAR_ACCESS_TOKEN", "not blank")
    @pytest.mark.parametrize("env_name", ["test", "random-env-name"])
    def test_disabled_in_unsupported_environment(self, mock_init, mock_app, env_name):
        with patch.object(rollbar_support.cfg, "SHERPA_ENV", env_name):
            enabled = enable_rollbar(mock_app)
            assert not mock_init.called
            assert not enabled

    @patch.object(rollbar_support.cfg, "ROLLBAR_ACCESS_TOKEN", None)
    @pytest.mark.parametrize("env_name", ["development", "production"])
    def test_disabled_when_access_token_is_none(self, mock_init, mock_app, env_name):
        with patch.object(rollbar_support.cfg, "SHERPA_ENV", env_name):
            enabled = enable_rollbar(mock_app)
            assert not mock_init.called
            assert not enabled

    @patch.object(rollbar_support.cfg, "ROLLBAR_ACCESS_TOKEN", "not blank")
    @pytest.mark.parametrize("env_name", ["development", "production"])
    def test_enabled_in_supported_env(self, mock_init, mock_app, env_name):
        with patch.object(rollbar_support.cfg, "SHERPA_ENV", env_name):
            enabled = enable_rollbar(mock_app)
            assert mock_init.called
            assert enabled
