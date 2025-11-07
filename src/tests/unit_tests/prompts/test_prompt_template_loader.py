from unittest.mock import patch, Mock, MagicMock
from sherpa_ai.prompts.prompt_template_loader import PromptTemplate
from pydantic import BaseModel
from langchain_core.language_models import BaseChatModel
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


# Tests for provider-specific formatting
@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_detect_provider_openai(mock_load_json):
    mock_load_json.return_value = mock_json_data
    template = PromptTemplate("./tests/data/prompts.json")
    
    # Mock OpenAI LLM
    mock_llm = MagicMock(spec=BaseChatModel)
    mock_llm._llm_type = "openai"
    
    provider = template._detect_provider(mock_llm)
    assert provider == "openai"


@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_detect_provider_anthropic(mock_load_json):
    mock_load_json.return_value = mock_json_data
    template = PromptTemplate("./tests/data/prompts.json")
    
    # Mock Anthropic LLM
    mock_llm = MagicMock(spec=BaseChatModel)
    mock_llm._llm_type = "anthropic"
    
    provider = template._detect_provider(mock_llm)
    assert provider == "anthropic"


@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_detect_provider_google(mock_load_json):
    mock_load_json.return_value = mock_json_data
    template = PromptTemplate("./tests/data/prompts.json")
    
    # Mock Google LLM
    mock_llm = MagicMock(spec=BaseChatModel)
    mock_llm._llm_type = "google"
    
    provider = template._detect_provider(mock_llm)
    assert provider == "google"


@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_detect_provider_cohere(mock_load_json):
    mock_load_json.return_value = mock_json_data
    template = PromptTemplate("./tests/data/prompts.json")
    
    # Mock Cohere LLM
    mock_llm = MagicMock(spec=BaseChatModel)
    mock_llm._llm_type = "cohere"
    
    provider = template._detect_provider(mock_llm)
    assert provider == "cohere"


@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_detect_provider_wrapped_model(mock_load_json):
    mock_load_json.return_value = mock_json_data
    template = PromptTemplate("./tests/data/prompts.json")
    
    # Mock wrapped LLM (e.g., ChatModelWithLogging)
    mock_inner_llm = MagicMock(spec=BaseChatModel)
    mock_inner_llm._llm_type = "openai"
    mock_llm = MagicMock(spec=BaseChatModel)
    mock_llm.llm = mock_inner_llm
    
    provider = template._detect_provider(mock_llm)
    assert provider == "openai"


@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_detect_provider_unknown(mock_load_json):
    mock_load_json.return_value = mock_json_data
    template = PromptTemplate("./tests/data/prompts.json")
    
    # Mock unknown LLM - _llm_type doesn't match any known provider
    mock_llm = MagicMock(spec=BaseChatModel)
    mock_llm._llm_type = "unknown_provider"
    # Make sure class name also doesn't match
    type(mock_llm).__name__ = "UnknownModel"
    
    provider = template._detect_provider(mock_llm)
    assert provider is None


@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_format_response_format_for_provider_openai(mock_load_json):
    mock_load_json.return_value = mock_json_data
    template = PromptTemplate("./tests/data/prompts.json")
    
    # Mock OpenAI LLM
    mock_llm = MagicMock(spec=BaseChatModel)
    mock_llm._llm_type = "openai"
    
    formatted = template.format_response_format_for_provider(
        prompt_parent_id="addition_prompts",
        prompt_id="add_numbers_text",
        version="1.0",
        llm=mock_llm
    )
    
    # Should return a Pydantic model class for OpenAI
    assert formatted is not None
    assert issubclass(formatted, BaseModel)
    # Verify the model has the expected fields
    assert hasattr(formatted, 'model_fields')
    assert 'result' in formatted.model_fields
    assert 'explanation' in formatted.model_fields


@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_format_response_format_for_provider_anthropic(mock_load_json):
    mock_load_json.return_value = mock_json_data
    template = PromptTemplate("./tests/data/prompts.json")
    
    # Mock Anthropic LLM
    mock_llm = MagicMock(spec=BaseChatModel)
    mock_llm._llm_type = "anthropic"
    
    formatted = template.format_response_format_for_provider(
        prompt_parent_id="addition_prompts",
        prompt_id="add_numbers_text",
        version="1.0",
        llm=mock_llm
    )
    
    # Should return tool definition format for Anthropic
    assert formatted is not None
    assert isinstance(formatted, dict)
    assert "tools" in formatted
    assert "tool_choice" in formatted
    assert len(formatted["tools"]) == 1
    assert formatted["tools"][0]["type"] == "function"
    assert formatted["tools"][0]["name"] == "addition_result"
    assert "input_schema" in formatted["tools"][0]
    assert formatted["tool_choice"]["type"] == "tool"
    assert formatted["tool_choice"]["name"] == "addition_result"


@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_format_response_format_for_provider_google(mock_load_json):
    mock_load_json.return_value = mock_json_data
    template = PromptTemplate("./tests/data/prompts.json")
    
    # Mock Google LLM
    mock_llm = MagicMock(spec=BaseChatModel)
    mock_llm._llm_type = "google"
    
    formatted = template.format_response_format_for_provider(
        prompt_parent_id="addition_prompts",
        prompt_id="add_numbers_text",
        version="1.0",
        llm=mock_llm
    )
    
    # Should return responseSchema format for Google
    assert formatted is not None
    assert isinstance(formatted, dict)
    assert "responseSchema" in formatted
    assert formatted["responseSchema"]["type"] == "object"
    assert "properties" in formatted["responseSchema"]


@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_format_response_format_for_provider_cohere(mock_load_json):
    mock_load_json.return_value = mock_json_data
    template = PromptTemplate("./tests/data/prompts.json")
    
    # Mock Cohere LLM
    mock_llm = MagicMock(spec=BaseChatModel)
    mock_llm._llm_type = "cohere"
    
    formatted = template.format_response_format_for_provider(
        prompt_parent_id="addition_prompts",
        prompt_id="add_numbers_text",
        version="1.0",
        llm=mock_llm
    )
    
    # Should return response_format format for Cohere
    assert formatted is not None
    assert isinstance(formatted, dict)
    assert "response_format" in formatted
    assert formatted["response_format"]["type"] == "object"
    assert "properties" in formatted["response_format"]


@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_format_response_format_for_provider_unknown(mock_load_json):
    mock_load_json.return_value = mock_json_data
    template = PromptTemplate("./tests/data/prompts.json")
    
    # Mock unknown LLM - _llm_type doesn't match any known provider
    mock_llm = MagicMock(spec=BaseChatModel)
    mock_llm._llm_type = "unknown_provider"
    # Make sure class name also doesn't match
    type(mock_llm).__name__ = "UnknownModel"
    
    formatted = template.format_response_format_for_provider(
        prompt_parent_id="addition_prompts",
        prompt_id="add_numbers_text",
        version="1.0",
        llm=mock_llm
    )
    
    # Should fallback to JSON Schema for unknown provider
    assert formatted is not None
    assert isinstance(formatted, dict)
    assert "type" in formatted or "json_schema" in formatted


@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_format_response_format_for_provider_none_llm(mock_load_json):
    mock_load_json.return_value = mock_json_data
    template = PromptTemplate("./tests/data/prompts.json")
    
    formatted = template.format_response_format_for_provider(
        prompt_parent_id="addition_prompts",
        prompt_id="add_numbers_text",
        version="1.0",
        llm=None
    )
    
    # Should fallback to JSON Schema when llm is None
    assert formatted is not None
    assert isinstance(formatted, dict)


@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_get_full_formatted_prompt_with_provider_openai(mock_load_json):
    mock_load_json.return_value = mock_json_data
    template = PromptTemplate("./tests/data/prompts.json")
    
    # Mock OpenAI LLM
    mock_llm = MagicMock(spec=BaseChatModel)
    mock_llm._llm_type = "openai"
    
    result = template.get_full_formatted_prompt(
        prompt_parent_id="addition_prompts",
        prompt_id="add_numbers_text",
        version="1.0",
        llm=mock_llm
    )
    
    assert result is not None
    assert "description" in result
    assert "content" in result
    assert "output_schema" in result
    # For OpenAI, output_schema should be a Pydantic model
    assert issubclass(result["output_schema"], BaseModel)


@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_get_full_formatted_prompt_with_provider_anthropic(mock_load_json):
    mock_load_json.return_value = mock_json_data
    template = PromptTemplate("./tests/data/prompts.json")
    
    # Mock Anthropic LLM
    mock_llm = MagicMock(spec=BaseChatModel)
    mock_llm._llm_type = "anthropic"
    
    result = template.get_full_formatted_prompt(
        prompt_parent_id="addition_prompts",
        prompt_id="add_numbers_text",
        version="1.0",
        llm=mock_llm
    )
    
    assert result is not None
    assert "description" in result
    assert "content" in result
    assert "output_schema" in result
    # For Anthropic, output_schema should be tool definition format
    assert isinstance(result["output_schema"], dict)
    assert "tools" in result["output_schema"]


@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_pydantic_to_json_schema(mock_load_json):
    mock_load_json.return_value = mock_json_data
    template = PromptTemplate("./tests/data/prompts.json")
    
    # Create a simple Pydantic model
    class TestModel(BaseModel):
        name: str
        age: int
    
    schema = template._pydantic_to_json_schema(TestModel)
    
    assert schema is not None
    assert isinstance(schema, dict)
    assert "properties" in schema
    assert "name" in schema["properties"]
    assert "age" in schema["properties"]
    assert schema["properties"]["name"]["type"] == "string"
    assert schema["properties"]["age"]["type"] == "integer"


@patch('sherpa_ai.prompts.prompt_loader.load_json')
def test_json_schema_to_pydantic(mock_load_json):
    mock_load_json.return_value = mock_json_data
    template = PromptTemplate("./tests/data/prompts.json")
    
    json_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"}
        },
        "required": ["name"]
    }
    
    Model = template._json_schema_to_pydantic(json_schema, "TestModel")
    
    assert Model is not None
    assert issubclass(Model, BaseModel)
    # Test creating an instance
    instance = Model(name="Alice", age=30)
    assert instance.name == "Alice"
    assert instance.age == 30
    # Test optional field
    instance2 = Model(name="Bob")
    assert instance2.name == "Bob"