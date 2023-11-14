import pytest

from sherpa_ai.config import AgentConfig


def test_all_parameters_parse_successfully():
    site = "https://www.google.com"
    input_str = f"Test input. --verbose --gsite {site} --do_reflect"

    parsed, config = AgentConfig.from_input(input_str)

    assert parsed == "Test input."
    assert config.verbose
    assert config.gsite == site
    assert config.do_reflect


def test_no_gsite_parses_successfully():
    input_str = "Test input. --verbose"

    parsed, config = AgentConfig.from_input(input_str)

    assert parsed == "Test input."
    assert config.verbose
    assert config.gsite is None


def test_parse_args_noise():
    site = "https://www.google.com"
    input_str = f"This is an input with -- but--should not be considered --verbose --verbosex --gsite {site} --do-reflect"  # noqa: E501

    with pytest.raises(ValueError):
        AgentConfig.from_input(input_str)
