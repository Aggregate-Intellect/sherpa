from slackapp.utils import get_qa_agent_from_config_file

from sherpa_ai.actions import ArxivSearch, GoogleSearch
from sherpa_ai.agents.qa_agent import QAAgent
from sherpa_ai.output_parsers.citation_validation import CitationValidation
from sherpa_ai.output_parsers.entity_validation import EntityValidation
from sherpa_ai.test_utils.data import get_test_data_file_path


def test_get_agent(get_test_data_file_path):  # noqa: F811
    config_filename = get_test_data_file_path(__file__, "test_get_agent.yaml")
    agent = get_qa_agent_from_config_file(config_filename)

    assert agent is not None
    assert type(agent) is QAAgent

    assert len(agent.actions) == 2
    assert type(agent.actions[0]) is ArxivSearch
    assert type(agent.actions[1]) is GoogleSearch
    assert len(agent.validations) == 2
    assert type(agent.validations[0]) is CitationValidation
    assert type(agent.validations[1]) is EntityValidation
