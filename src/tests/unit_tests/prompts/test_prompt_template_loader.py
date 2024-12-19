import pytest
from unittest.mock import patch, MagicMock
from sherpa_ai.prompts.prompt_template_loader import PromptTemplate


mock_json_data = {
    "addition_prompts": [
        {
            "name": "addition_prompts",
            "description": "prompt to add numbers and return structured output",
            "prompts": [
                {
                    "name": "add_numbers",
                    "version": "1.0",
                    "type": "chat",
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
    ]
}

@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_format_prompt(mock_load_json):
    mock_load_json.return_value = mock_json_data
    template = PromptTemplate("./tests/data/prompts.json")
    
    # Test formatting prompt with variables
    variables = {"first_num": 15, "second_num": 25}
    formatted_prompt = template.format_prompt("addition_prompts", "add_numbers", "1.0", variables)
    
    assert formatted_prompt == [
        {"role": "system", "content": "You are a helpful assistant that performs simple arithmetic operations."},
        {"role": "user", "content": "Add 15 and 25"}
    ]

@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_get_full_formatted_prompt(mock_load_json):
    mock_load_json.return_value = mock_json_data
    template = PromptTemplate("./tests/data/prompts.json")
    
    # Test getting full formatted prompt
    variables = {"first_num": 15, "second_num": 25}
    full_prompt = template.get_full_formatted_prompt("addition_prompts", "add_numbers", "1.0", variables)

    assert full_prompt["description"] == "prompt to add numbers and return structured output"
    assert full_prompt["content"] == [
        {"role": "system", "content": "You are a helpful assistant that performs simple arithmetic operations."},
        {"role": "user", "content": "Add 15 and 25"}
    ]
    assert full_prompt["output_schema"] == {
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

@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_format_prompt_with_default_variables(mock_load_json):
    mock_load_json.return_value = mock_json_data
    template = PromptTemplate("./tests/data/prompts.json")
    
    # Test formatting prompt with no variables (should use default)
    formatted_prompt = template.format_prompt("addition_prompts", "add_numbers", "1.0")
    
    assert formatted_prompt == [
        {"role": "system", "content": "You are a helpful assistant that performs simple arithmetic operations."},
        {"role": "user", "content": "Add 5 and 10"}
    ]