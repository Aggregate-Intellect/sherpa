import pytest

from sherpa_ai.config import AgentConfig


def test_parse_args():
    site = "https://www.google.com"
    input_str = f"Test input. --verbose --verbosex --gsite {site}"

    config = AgentConfig.from_input(input_str)

    assert config.verbose
    assert config.verbosex
    assert config.gsite == site


def test_parse_args_partial():
    input_str = "Test input. --verbose"

    config = AgentConfig.from_input(input_str)

    assert config.verbose
    assert config.gsite is None


def test_parse_args_noise():
    site = "https://www.google.com"
    input_str = f"This is an input with -- but--should not be considered --verbose --verbosex --gsite {site} --do-reflect"  # noqa: E501

    with pytest.raises(ValueError):
        AgentConfig.from_input(input_str)
