import pytest
from unittest.mock import patch, MagicMock
from sherpa_ai.prompts.prompt_loader import PromptLoader
from sherpa_ai.prompts.prompt_loader import JsonToObject


# Mock JSON data to simulate prompts.json
mock_json_data = {
    "addition_prompts": [
        {
            "name": "add",
            "description": "prompt to add numbers and return structured output",
            "schema": {
                "prompts": [
                    {
                        "name": "add_numbers",
                        "version": "1.0",
                        "type": "object",
                        "description": "prompt to add numbers and return structured output",
                        "content": [
                            {"role": "system", "content": "You are a helpful assistant that performs simple arithmetic operations."},
                            {"role": "user", "content": "Add {first_num} and {second_num}"}
                        ],
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
        }
    ]
}


@pytest.fixture
def mock_json():
    # Return a mock JsonToObject instance mimicking JSON object conversion
    mock_object = JsonToObject()
    mock_object.addition_prompts = mock_json_data["addition_prompts"]
    return mock_object


@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_prompt_loader_process_prompts(mock_load_json, mock_json):
    # Mock loading of JSON
    mock_load_json.return_value = mock_json_data
    
    # Initialize PromptLoader
    loader = PromptLoader("./tests/data/prompts.json")
    
    # Test processing prompts
    assert loader.prompts["addition_prompts"][0].name == "add_numbers"
    assert loader.prompts["addition_prompts"][0].version == "1.0"
    assert len(loader.prompts["addition_prompts"]) == 1


@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_get_prompt(mock_load_json, mock_json):
    mock_load_json.return_value = mock_json_data
    loader = PromptLoader("./tests/data/prompts.json")
    
    # Test fetching a prompt by wrapper, name, and version
    prompt = loader.get_prompt("addition_prompts", "add_numbers", "1.0")
    assert prompt.name == "add_numbers"
    assert prompt.version == "1.0"


@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_get_prompt_content(mock_load_json):
    mock_load_json.return_value = mock_json_data
    loader = PromptLoader("./tests/data/prompts.json")
    
    # Test fetching prompt content
    content = loader.get_prompt_content("addition_prompts", "add_numbers", "1.0")
    assert str(content) == str([
        {"role": "system", "content": "You are a helpful assistant that performs simple arithmetic operations."},
        {"role": "user", "content": "Add {first_num} and {second_num}"}
    ])


@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_get_prompt_output_schema(mock_load_json):
    mock_load_json.return_value = mock_json_data
    loader = PromptLoader("./tests/data/prompts.json")
    
    # Test fetching output schema
    output_schema = loader.get_prompt_output_schema("addition_prompts", "add_numbers", "1.0")
    assert str(output_schema) == str({
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
    })