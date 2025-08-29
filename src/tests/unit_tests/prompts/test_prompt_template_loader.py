from unittest.mock import patch, Mock
from sherpa_ai.prompts.prompt_template_loader import PromptTemplate
import json


# Mock JSON data to simulate prompts.json with the 'versions' list
mock_json_data = [
    {
        "prompt_parent_id": "addition_prompts",
        "description": "prompt to add numbers and return structured output",
        "prompts": [
            {
                "prompt_id": "add_numbers_text",
                "description": "prompt to add numbers as text",
                "versions": [
                    {
                        "version": "1.0",
                        "change_log": "Initial version for text addition",
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
                        "version": "2.0",
                        "change_log": "Version with list of strings",
                        "type": "text",
                        "content": ["Add", "{first_num}", "and", "{second_num}"],
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
                "prompt_id": "add_numbers_chat",
                "description": "prompt to add numbers as chat",
                "versions": [
                    {
                        "version": "1.0",
                        "change_log": "Initial version for chat addition",
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
                        "change_log": "Initial version for JSON addition",
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
def test_format_prompt_text_single_string(mock_load_json):
    mock_load_json.return_value = mock_json_data
    template = PromptTemplate("./tests/data/prompts.json")
    
    variables = {"first_num": 15, "second_num": 25}
    formatted_prompt = template.format_prompt("addition_prompts", "add_numbers_text", "1.0", variables)
    
    assert formatted_prompt == "Add 15 and 25"


@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_format_prompt_text_list_of_strings(mock_load_json):
    mock_load_json.return_value = mock_json_data
    template = PromptTemplate("./tests/data/prompts.json")
    
    variables = {"first_num": 15, "second_num": 25}
    formatted_prompt = template.format_prompt("addition_prompts", "add_numbers_text", "2.0", variables)
    
    assert formatted_prompt == "Add\n15\nand\n25"


@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_format_prompt_text_default_variables(mock_load_json):
    mock_load_json.return_value = mock_json_data
    template = PromptTemplate("./tests/data/prompts.json")
    
    formatted_prompt = template.format_prompt("addition_prompts", "add_numbers_text", "1.0")
    
    assert formatted_prompt == "Add 5 and 10"


@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_format_prompt_text_list_default_variables(mock_load_json):
    mock_load_json.return_value = mock_json_data
    template = PromptTemplate("./tests/data/prompts.json")
    
    formatted_prompt = template.format_prompt("addition_prompts", "add_numbers_text", "2.0")
    
    assert formatted_prompt == "Add\n5\nand\n10"


@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_get_full_formatted_prompt_text_single_string(mock_load_json):
    mock_load_json.return_value = mock_json_data
    template = PromptTemplate("./tests/data/prompts.json")
    
    variables = {"first_num": 15, "second_num": 25}
    full_prompt = template.get_full_formatted_prompt("addition_prompts", "add_numbers_text", "1.0", variables)
    
    assert full_prompt["description"] == "prompt to add numbers as text"
    assert full_prompt["content"] == "Add 15 and 25"
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
def test_get_full_formatted_prompt_text_list_of_strings(mock_load_json):
    mock_load_json.return_value = mock_json_data
    template = PromptTemplate("./tests/data/prompts.json")
    
    variables = {"first_num": 15, "second_num": 25}
    full_prompt = template.get_full_formatted_prompt("addition_prompts", "add_numbers_text", "2.0", variables)
    
    assert full_prompt["description"] == "prompt to add numbers as text"
    assert full_prompt["content"] == "Add\n15\nand\n25"
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


def test_dynamic_enum_in_response_schema():
    template = PromptTemplate("tests/data/prompts.json")

    # Test the math addition prompt with dynamic enum values for output_format
    result = template.format_response_format(
        prompt_parent_id="math_prompts",
        prompt_id="addition_with_allowed_output_format",
        version="1.0",
        variables={
            "a": 7,
            "b": 8,
            "allowed_output_formats": ["plain_text", "markdown", "json"]
        }
    )

    assert result is not None
    assert "json_schema" in result

    # Check that the enum values were substituted
    schema = result["json_schema"]["schema"]
    enum_values = schema["properties"]["output_format"]["enum"]
    assert enum_values == ["plain_text", "markdown", "json"]

    full_result = template.get_full_formatted_prompt(
        prompt_parent_id="math_prompts",
        prompt_id="addition_with_allowed_output_format",
        version="1.0",
        variables={
            "a": 10,
            "b": 20,
            "allowed_output_formats": ["csv", "yaml"]
        }
    )

    assert full_result is not None
    assert "output_schema" in full_result

    output_schema = full_result["output_schema"]["json_schema"]["schema"]
    output_enum_values = output_schema["properties"]["output_format"]["enum"]
    assert output_enum_values == ["csv", "yaml"]
    # Content includes variable substitutions; list prints as Python list string
    assert "A: 10" in full_result["content"]
    assert "B: 20" in full_result["content"]
    assert "['csv', 'yaml']" in full_result["content"]