import pytest
from unittest.mock import patch
from sherpa_ai.prompts.prompt_loader import PromptLoader, JsonToObject


# Mock JSON data to simulate prompts.json
mock_json_data = {
    "addition_prompts": [
        {
            "name": "addition_prompts",
            "description": "prompt to add numbers and return structured output",
            "prompts": [
                {
                    "name": "add_numbers",
                    "description": "prompt to add numbers and return structured output",
                    "version": "1.0",
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
        }
    ]
}


@pytest.fixture
def mock_json():
    mock_object = JsonToObject({})
    mock_object.addition_prompts = mock_json_data["addition_prompts"]
    return mock_object


@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_prompt_loader_process_prompts(mock_load_json):
    mock_load_json.return_value = mock_json_data
    loader = PromptLoader("./tests/data/prompts.json")

    print("&"*70)
    print(loader.prompts)
    print("&"*70)

    prompts = loader.prompts[0].prompts  # Adjust if necessary
    assert prompts[0].name == "add_numbers"
    assert prompts[0].version == "1.0"
    assert len(prompts) == 1


@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_get_prompt(mock_load_json):
    mock_load_json.return_value = mock_json_data
    loader = PromptLoader("./tests/data/prompts.json")

    prompt = loader.get_prompt("addition_prompts", "add_numbers", "1.0")
    assert prompt.name == "add_numbers"
    assert prompt.version == "1.0"


@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_get_prompt_content(mock_load_json):
    mock_load_json.return_value = mock_json_data
    loader = PromptLoader("./tests/data/prompts.json")

    content = loader.get_prompt_content("addition_prompts", "add_numbers", "1.0")
    assert content.content == "Add {first_num} and {second_num}"


@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_get_prompt_output_schema(mock_load_json):
    mock_load_json.return_value = mock_json_data
    loader = PromptLoader("./tests/data/prompts.json")

    output_schema = loader.get_prompt_output_schema("addition_prompts", "add_numbers", "1.0")
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
