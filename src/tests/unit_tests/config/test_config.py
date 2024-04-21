from unittest.mock import mock_open, patch

import sherpa_ai.config as cfg
from sherpa_ai.config import current_app_revision_from_file_or_git


@patch("sherpa_ai.config.path.exists", return_value=True)
@patch("builtins.open", mock_open(read_data="why hello!   "))
def test_revision_from_file(mock_open):
    with mock_open:
        result = current_app_revision_from_file_or_git()
        assert result == "why hello!"  # trailing whitespace is stripped


@patch("sherpa_ai.config.path.exists", return_value=False)
@patch("sherpa_ai.config.current_git_revision_short_hash", return_value="abcd")
def test_revision_from_git(mock_current_git_revision_short_hash, mock_exists):
    with mock_current_git_revision_short_hash, mock_exists:
        result = current_app_revision_from_file_or_git()
        assert result == "abcd"


@patch("sherpa_ai.config.path.exists", return_value=False)
@patch("sherpa_ai.config.current_git_revision_short_hash", return_value=None)
def test_revision_unknown(mock_current_git_revision_short_hash, mock_exists):
    with mock_current_git_revision_short_hash, mock_exists:
        result = current_app_revision_from_file_or_git()
        assert result is None


def test_sensitive_configuration_values():
    assert cfg.SENSITIVE_SETTINGS_AND_SECRETS is not None
    assert len(cfg.SENSITIVE_SETTINGS_AND_SECRETS) > 0
