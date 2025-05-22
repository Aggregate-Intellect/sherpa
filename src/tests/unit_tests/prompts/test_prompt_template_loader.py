from unittest.mock import patch
from sherpa_ai.prompts.prompt_template_loader import PromptTemplate


# Mock JSON data to simulate prompts.json with the 'versions' list
mock_json_data = [
    {
        "prompt_parent_id": "addition_prompts",
        "description": "prompt to add numbers and return structured output",
        "prompts": [
            {
                "prompt_id": "add_numbers_chat",
                "description": "prompt to add numbers as chat",
                "versions": [
                    {
                        "version": "1.0",
                        "change_log": "Initial version",
                        "type": "chat",
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
            },
            {
                "prompt_id": "add_numbers_json",
                "description": "prompt to add numbers as JSON",
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

@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_format_prompt_chat(mock_load_json):
    mock_load_json.return_value = mock_json_data
    template = PromptTemplate("./tests/data/prompts.json")
    
    variables = {"first_num": 15, "second_num": 25}
    formatted_prompt = template.format_prompt("addition_prompts", "add_numbers_chat", "1.0", variables)
    
    assert formatted_prompt == [
        {"role": "system", "content": "You are a helpful assistant that performs simple arithmetic operations."},
        {"role": "user", "content": "Add 15 and 25"}
    ]

@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_format_prompt_json(mock_load_json):
    mock_load_json.return_value = mock_json_data
    template = PromptTemplate("./tests/data/prompts.json")
    
    variables = {"first_num": 15, "second_num": 25}
    formatted_prompt = template.format_prompt("addition_prompts", "add_numbers_json", "1.0", variables)

    assert formatted_prompt == {
        "operation": "add",
        "first_number": "15",
        "second_number": "25"
    }

@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_get_full_formatted_prompt_chat(mock_load_json):
    mock_load_json.return_value = mock_json_data
    template = PromptTemplate("./tests/data/prompts.json")

    variables = {"first_num": 15, "second_num": 25}
    full_prompt = template.get_full_formatted_prompt("addition_prompts", "add_numbers_chat", "1.0", variables)

    assert full_prompt["description"] == "prompt to add numbers as chat"
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
def test_get_full_formatted_prompt_json(mock_load_json):
    mock_load_json.return_value = mock_json_data
    template = PromptTemplate("./tests/data/prompts.json")

    variables = {"first_num": 15, "second_num": 25}
    full_prompt = template.get_full_formatted_prompt("addition_prompts", "add_numbers_json", "1.0", variables)

    assert full_prompt["description"] == "prompt to add numbers as JSON"
    assert full_prompt["content"] == {
        "operation": "add",
        "first_number": "15",
        "second_number": "25"
    }
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
def test_format_prompt_with_default_variables_chat(mock_load_json):
    mock_load_json.return_value = mock_json_data
    template = PromptTemplate("./tests/data/prompts.json")
    
    formatted_prompt = template.format_prompt("addition_prompts", "add_numbers_chat", "1.0")
    
    assert formatted_prompt == [
        {"role": "system", "content": "You are a helpful assistant that performs simple arithmetic operations."},
        {"role": "user", "content": "Add 5 and 10"}
    ]

@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_format_prompt_with_default_variables_json(mock_load_json):
    mock_load_json.return_value = mock_json_data
    template = PromptTemplate("./tests/data/prompts.json")
    
    formatted_prompt = template.format_prompt("addition_prompts", "add_numbers_json", "1.0")
    
    assert formatted_prompt == {
        "operation": "add",
        "first_number": "5",
        "second_number": "10"
    }