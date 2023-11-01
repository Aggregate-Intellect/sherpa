import pytest

from sherpa_ai.config import AgentConfig
from sherpa_ai.tools import ContextTool, SearchTool
from langchain import GoogleSerperAPIWrapper
from sherpa_ai.actions.google_search import GoogleSearch
from langchain.llms import OpenAI
import sherpa_ai.config as cfg


def test_parse_args():
    site = "https://www.google.com"
    input_str = f"Test input. --verbose --gsite {site}"

    parsed, config = AgentConfig.from_input(input_str)

    assert parsed == "Test input."
    assert config.verbose
    assert config.gsite == site


def test_parse_args_partial():
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


def test_gsite_google_search():
    site = "https://www.google.com"
    input_str = f"Test input. --verbose --gsite {site}"

    question, config = AgentConfig.from_input(input_str)

    assert config.gsite == site

    role_description =  "The programmer receives requirements about a program and write it"
    
    task = """We need to render a highly complex 3D image on the solar system. We can use any publicly avaliable
    resources to achieve this task."""  # noqa: E501
    
    llm = OpenAI(openai_api_key=cfg.OPENAI_API_KEY, temperature=0)
    
    google_search = GoogleSearch(role_description=role_description, task=task, llm=llm, config=config)

    query = "What is the weather today?"
    
    updated_query = google_search.config_gsite_query(query)
    
    assert site in updated_query
