
import pytest
from unittest.mock import patch
from sherpa_ai.prompts.prompt_loader import PromptLoader, JsonToObject
from sherpa_ai.prompts.Base import PromptGroup


# Mock JSON data to simulate prompts.json with the 'versions' list
mock_json_data = [
    {
        "prompt_parent_id": "addition_prompts",
        "description": "prompt to add numbers and return structured output",
        "prompts": [
            {
                "prompt_id": "add_numbers_text",
                "description": "prompt to add numbers and return structured output as text",
                "versions": [ 
                    {
                        "version": "1.0",
                        "change_log": "Initial version",
                        "type": "text",
                        "content": "Add {first_num} and {second_num}",
                        "variables": {"first_num": 5, "second_num": 10},
                        "response_format": {
                            "type": "json_schema",
                            "json_schema": {
                                "name": "addition_result",
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "result": {"type": "number"},
                                        "explanation": {"type": "string"}
                                    },
                                    "required": ["result", "explanation"]
                                }
                            }
                        }
                    }
                ]
            },
            {
                "prompt_id": "add_numbers_json",
                "description": "prompt to add numbers and return structured output as JSON",
                "versions": [
                    {
                        "version": "1.0",
                        "change_log": "Initial version",
                        "type": "json",
                        "content": {
                            "operation": "add",
                            "first_number": "{first_num}",
                            "second_number": "{second_num}"
                        },
                        "variables": {"first_num": 5, "second_num": 10},
                        "response_format": {
                            "type": "json_schema",
                            "json_schema": {
                                "name": "addition_result",
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "result": {"type": "number"},
                                        "explanation": {"type": "string"}
                                    },
                                    "required": ["result", "explanation"]
                                }
                            }
                        }
                    }
                ]
            }
        ]
    }
]


@pytest.fixture
def mock_json_object():
    return JsonToObject(mock_json_data)


@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_prompt_loader_process_prompts(mock_load_json):
    mock_load_json.return_value = mock_json_data
    loader = PromptLoader("./tests/data/prompts.json")

    assert len(loader.prompts) == 1
    prompt_group = loader.prompts[0]
    assert isinstance(prompt_group, PromptGroup)
    assert prompt_group.prompt_parent_id == "addition_prompts"

    prompts = prompt_group.prompts
    assert len(prompts) == 2
    assert prompts[0].prompt_id == "add_numbers_text"
    assert prompts[0].versions[0].version == "1.0"
    assert isinstance(prompts[0].versions[0].content, str)
    assert prompts[1].prompt_id == "add_numbers_json"
    assert prompts[1].versions[0].version == "1.0"
    assert isinstance(prompts[1].versions[0].content, dict)


@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_get_prompt_version_text(mock_load_json):
    mock_load_json.return_value = mock_json_data
    loader = PromptLoader("./tests/data/prompts.json")

    prompt_version = loader.get_prompt_version("addition_prompts", "add_numbers_text", "1.0")
    assert prompt_version.version == "1.0"
    assert isinstance(prompt_version.content, str)


@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_get_prompt_version_json(mock_load_json):
    mock_load_json.return_value = mock_json_data
    loader = PromptLoader("./tests/data/prompts.json")

    prompt_version = loader.get_prompt_version("addition_prompts", "add_numbers_json", "1.0")
    assert prompt_version.version == "1.0"
    assert isinstance(prompt_version.content, dict)

@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_get_prompt_content_text(mock_load_json):
    mock_load_json.return_value = mock_json_data
    loader = PromptLoader("./tests/data/prompts.json")

    content = loader.get_prompt_content("addition_prompts", "add_numbers_text", "1.0")
    assert content == "Add {first_num} and {second_num}"

@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_get_prompt_content_json(mock_load_json):
    mock_load_json.return_value = mock_json_data
    loader = PromptLoader("./tests/data/prompts.json")

    content = loader.get_prompt_content("addition_prompts", "add_numbers_json", "1.0")
    assert content == {
        "operation": "add",
        "first_number": "{first_num}",
        "second_number": "{second_num}"
    }

@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_get_prompt_output_schema(mock_load_json):
    mock_load_json.return_value = mock_json_data
    loader = PromptLoader("./tests/data/prompts.json")

    output_schema = loader.get_prompt_output_schema("addition_prompts", "add_numbers_json", "1.0")
    assert output_schema == {
        "type": "json_schema",
        "json_schema": {
            "name": "addition_result",
            "schema": {
                "type": "object",
                "properties": {
                    "result": {"type": "number"},
                    "explanation": {"type": "string"}
                },
                "required": ["result", "explanation"]
            }
        }
    }