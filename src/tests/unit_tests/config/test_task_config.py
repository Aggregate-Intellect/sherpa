import pytest

from sherpa_ai.config import AgentConfig


def test_config_parses_all_parameters_correctly():
    site = "https://www.google.com"
    input_str = f"Test input. --verbose --gsite {site} --do-reflect"

    parsed, config = AgentConfig.from_input(input_str)

    assert parsed == "Test input."
    assert config.verbose
    assert config.gsite == site
    assert config.do_reflect
    assert config.search_domains == ["https://www.google.com"]
    assert config.invalid_domain == []

def test_config_parse_multiple_gsites_correctly():
    site = "https://www.google.com, https://www.langchain.com, https://openai.com, /data/Python.html, 532"
    input_str = f"Test input. --verbose --gsite {site} --do-reflect"

    parsed, config = AgentConfig.from_input(input_str)

    assert parsed == "Test input."
    assert config.verbose
    assert config.gsite == site
    assert config.do_reflect
    assert config.search_domains == ["https://www.google.com", "https://www.langchain.com", "https://openai.com"]
    assert config.invalid_domain == ["/data/Python.html", "532"]


def test_config_parses_input_and_verbose_options_with_no_gsite():
    input_str = "Test input. --verbose"

    parsed, config = AgentConfig.from_input(input_str)

    assert parsed == "Test input."
    assert config.verbose
    assert config.gsite is None


def test_config_raises_exception_for_unsupported_options():
    site = "https://www.google.com"
    input_str = f"This is an input with -- but--should not be considered --verbose --verbosex --gsite {site} --do-reflect"  # noqa: E501

    with pytest.raises(ValueError):
        AgentConfig.from_input(input_str)
