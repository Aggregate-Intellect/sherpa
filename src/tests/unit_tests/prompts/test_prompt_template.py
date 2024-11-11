import pytest
from unittest.mock import patch, MagicMock
from sherpa_ai.prompts.prompt_template import PromptTemplate


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

    
    assert str(full_prompt["description"]) == "prompt to add numbers and return structured output"
    assert str(full_prompt["content"]) == str([
        {"role": "system", "content": "You are a helpful assistant that performs simple arithmetic operations."},
        {"role": "user", "content": "Add 15 and 25"}
    ])
    assert str(full_prompt["output_schema"]) == str({
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
