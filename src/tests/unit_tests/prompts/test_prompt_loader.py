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
                    "name": "add_numbers_text",
                    "description": "prompt to add numbers and return structured output as text",
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
                },
                {
                    "name": "add_numbers_json",
                    "description": "prompt to add numbers and return structured output as JSON",
                    "version": "1.0",
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


@pytest.fixture
def mock_json():
    mock_object = JsonToObject({})
    mock_object.addition_prompts = mock_json_data["addition_prompts"]
    return mock_object


@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_prompt_loader_process_prompts(mock_load_json):
    mock_load_json.return_value = mock_json_data
    loader = PromptLoader("./tests/data/prompts.json")

    prompts = loader.prompts[0].prompts
    assert len(prompts) == 2
    assert prompts[0].name == "add_numbers_text"
    assert prompts[0].version == "1.0"
    assert isinstance(prompts[0].content, str)
    assert prompts[1].name == "add_numbers_json"
    assert prompts[1].version == "1.0"
    assert isinstance(prompts[1].content, dict)

@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_get_prompt_text(mock_load_json):
    mock_load_json.return_value = mock_json_data
    loader = PromptLoader("./tests/data/prompts.json")

    prompt = loader.get_prompt("addition_prompts", "add_numbers_text", "1.0")
    assert prompt.name == "add_numbers_text"
    assert prompt.version == "1.0"
    assert isinstance(prompt.content, str)

@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_get_prompt_json(mock_load_json):
    mock_load_json.return_value = mock_json_data
    loader = PromptLoader("./tests/data/prompts.json")

    prompt = loader.get_prompt("addition_prompts", "add_numbers_json", "1.0")
    assert prompt.name == "add_numbers_json"
    assert prompt.version == "1.0"
    assert isinstance(prompt.content, dict)

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