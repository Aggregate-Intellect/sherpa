import pytest

from sherpa_ai.config import AgentConfig


def test_config_parses_all_parameters_correctly():
    site = "https://www.google.com"
    input_str = f"Test input. --concise --gsite {site} --do-reflect"

    parsed, config = AgentConfig.from_input(input_str)

    assert parsed == "Test input."
    assert not config.verbose
    assert config.gsite == site
    assert config.do_reflect


def test_config_parses_input_and_concise_options_with_no_gsite():
    input_str = "Test input. --concise"

    parsed, config = AgentConfig.from_input(input_str)

    assert parsed == "Test input."
    assert not config.verbose
    assert config.gsite is None


def test_config_raises_exception_for_unsupported_options():
    site = "https://www.google.com"
    input_str = f"This is an input with -- but--should not be considered --concise --verbosex --gsite {site} --do-reflect"  # noqa: E501

    with pytest.raises(ValueError):
        AgentConfig.from_input(input_str)
