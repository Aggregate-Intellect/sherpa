"""Prompt template loading and formatting module for Sherpa AI.

This module provides functionality for loading prompt templates and formatting
them with variables. It extends the base PromptLoader to add variable
substitution capabilities for different prompt types.
"""

from typing import Dict, List, Optional, Union, Any, Type
from sherpa_ai.prompts.Base import ChatPromptVersion, TextPromptVersion, JsonPromptVersion
from sherpa_ai.prompts.prompt_loader import PromptLoader
import copy
from pydantic import BaseModel, create_model
from langchain_core.language_models import BaseChatModel

class PromptTemplate(PromptLoader):
    """Template loader and formatter for prompts.

    This class extends PromptLoader to add variable substitution capabilities.
    It can format text, chat, and JSON prompts by replacing placeholders
    with actual values.

    Example:
        >>> template = PromptTemplate("prompts.json")
        >>> formatted = template.format_prompt(
        ...     prompt_parent_id="chat",
        ...     prompt_id="greeting",
        ...     version="1.0",
        ...     variables={"name": "Alice"}
        ... )
        >>> print(formatted[0]["content"])
        'Hello Alice!'
    """

    def __init__(self, json_file_path: str):
        """Initialize the prompt template loader.

        Args:
            json_file_path (str): Path to JSON file containing prompt templates.
        """
        super().__init__(json_file_path)

    def _detect_provider(self, llm: Optional[BaseChatModel]) -> Optional[str]:
        """Detect the LLM provider from an LLM instance.

        This method identifies the provider by checking the _llm_type attribute
        and class name as fallback.

        Args:
            llm (Optional[BaseChatModel]): The LLM instance to detect.

        Returns:
            Optional[str]: Provider name ('openai', 'anthropic', 'google', 'cohere')
                or None if provider cannot be detected.

        Example:
            >>> template = PromptTemplate("prompts.json")
            >>> llm = ChatOpenAI()
            >>> provider = template._detect_provider(llm)
            >>> print(provider)
            'openai'
        """
        if llm is None:
            return None

        # Check for wrapped models (e.g., ChatModelWithLogging)
        actual_llm = llm
        if hasattr(llm, 'llm'):
            actual_llm = llm.llm

        # Try to get provider from _llm_type attribute
        if hasattr(actual_llm, '_llm_type'):
            llm_type = actual_llm._llm_type.lower()
            if 'openai' in llm_type:
                return 'openai'
            elif 'anthropic' in llm_type or 'claude' in llm_type or 'bedrock' in llm_type:
                return 'anthropic'
            elif 'google' in llm_type or 'gemini' in llm_type or 'vertexai' in llm_type:
                return 'google'
            elif 'cohere' in llm_type:
                return 'cohere'

        # Fallback to class name inspection
        class_name = actual_llm.__class__.__name__.lower()
        if 'openai' in class_name:
            return 'openai'
        elif 'anthropic' in class_name or 'claude' in class_name:
            return 'anthropic'
        elif 'google' in class_name or 'gemini' in class_name or 'vertex' in class_name:
            return 'google'
        elif 'cohere' in class_name:
            return 'cohere'

        return None

    def _pydantic_to_json_schema(self, pydantic_model: Type[BaseModel]) -> Dict[str, Any]:
        """Convert a Pydantic model to JSON Schema.

        This method uses Pydantic's built-in model_json_schema() method to
        convert a Pydantic model to JSON Schema format.

        Args:
            pydantic_model (Type[BaseModel]): The Pydantic model class to convert.

        Returns:
            Dict[str, Any]: JSON Schema representation of the Pydantic model.

        Example:
            >>> from pydantic import BaseModel
            >>> class User(BaseModel):
            ...     name: str
            ...     age: int
            >>> template = PromptTemplate("prompts.json")
            >>> schema = template._pydantic_to_json_schema(User)
            >>> print(schema['properties']['name']['type'])
            'string'
        """
        if not issubclass(pydantic_model, BaseModel):
            raise ValueError(f"Expected a Pydantic BaseModel, got {type(pydantic_model)}")

        return pydantic_model.model_json_schema()

    def _json_schema_to_pydantic(self, json_schema: Dict[str, Any], model_name: str = "DynamicModel") -> Type[BaseModel]:
        """Convert a JSON Schema to a Pydantic model.

        This method dynamically creates a Pydantic model from a JSON Schema.
        Note: This is a simplified implementation and may not handle all
        JSON Schema features.

        Args:
            json_schema (Dict[str, Any]): The JSON Schema to convert.
            model_name (str): Name for the generated Pydantic model class.

        Returns:
            Type[BaseModel]: A dynamically created Pydantic model class.

        Example:
            >>> template = PromptTemplate("prompts.json")
            >>> schema = {
            ...     "type": "object",
            ...     "properties": {
            ...         "name": {"type": "string"},
            ...         "age": {"type": "integer"}
            ...     },
            ...     "required": ["name"]
            ... }
            >>> Model = template._json_schema_to_pydantic(schema, "User")
            >>> instance = Model(name="Alice", age=30)
        """
        if json_schema.get("type") != "object":
            raise ValueError("JSON Schema must be of type 'object' to convert to Pydantic model")

        properties = json_schema.get("properties", {})
        required = set(json_schema.get("required", []))

        # Map JSON Schema types to Python types
        type_mapping = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        field_definitions = {}
        for field_name, field_schema in properties.items():
            field_type = field_schema.get("type", "string")
            python_type = type_mapping.get(field_type, str)

            # Handle Optional fields
            if field_name not in required:
                field_definitions[field_name] = (Optional[python_type], None)
            else:
                field_definitions[field_name] = (python_type, ...)

        return create_model(model_name, **field_definitions)

    def format_prompt(
        self,
        prompt_parent_id: str,
        prompt_id: str, # Changed from name to prompt_id
        version: str,
        variables: Optional[Dict[str, Union[str, int, float]]] = None
    ) -> Optional[Union[str, List[Dict[str, str]], Dict]]:
        """Format a prompt by replacing variables with values.

        This method loads a prompt template and replaces any variable
        placeholders with provided values. It handles different prompt types
        (text, chat, JSON) appropriately.

        Args:
            prompt_parent_id (str): Name of the wrapper containing the prompt.
            prompt_id (str): ID of the prompt to format.
            version (str): Version of the prompt to format.
            variables (Optional[Dict[str, Union[str, int, float]]]): Values to
                substitute in the prompt. If None, uses defaults from JSON.

        Returns:
            Optional[Union[str, List[Dict[str, str]], Dict]]: Formatted prompt
                content if found and successfully formatted, None otherwise.

        Example:
            >>> template = PromptTemplate("prompts.json")
            >>> formatted = template.format_prompt(
            ...     prompt_parent_id="text",
            ...     prompt_id="search",
            ...     version="1.0",
            ...     variables={"query": "python programming"}
            ... )
            >>> print(formatted)
            'Search for: python programming'
        """
        # We need to get the specific prompt version object
        prompt_version_obj = self.get_prompt_version(prompt_parent_id, prompt_id, version)

        if not prompt_version_obj:
            return None

        prompt_variables = prompt_version_obj.variables or {}
        final_variables = prompt_variables.copy()

        if variables:
            final_variables.update(variables)

        # Format the prompt content
        if isinstance(prompt_version_obj, ChatPromptVersion):
            formatted_prompt = []
            for message in prompt_version_obj.content:
                role = message.get("role")
                text = message.get("content", "")

                # Replace placeholders with variables
                for var_name, var_value in final_variables.items():
                    placeholder = f"{{{var_name}}}"
                    if placeholder in text:
                        text = text.replace(placeholder, str(var_value))

                formatted_prompt.append({"role": role, "content": text})
            return formatted_prompt

        elif isinstance(prompt_version_obj, TextPromptVersion):
            content = prompt_version_obj.content
            
            # Handle array content
            if isinstance(content, list):
                content = "\n".join(str(item) for item in content) if content else ""
            
            for var_name, var_value in final_variables.items():
                placeholder = f"{{{var_name}}}"
                if placeholder in content:
                    content = content.replace(placeholder, str(var_value))
            return content

        elif isinstance(prompt_version_obj, JsonPromptVersion):
            import copy
            formatted_prompt = copy.deepcopy(prompt_version_obj.content)
            def replace_in_dict(data: Dict) -> Dict:
                """Recursively replace variables in dictionary values.

                Args:
                    data (Dict): Dictionary to process.

                Returns:
                    Dict: Dictionary with variables replaced.
                """
                for key, value in data.items():
                    if isinstance(value, str):
                        for var_name, var_value in final_variables.items():
                            placeholder = f"{{{var_name}}}"
                            if placeholder in value:
                                data[key] = value.replace(placeholder, str(var_value))
                    elif isinstance(value, dict):
                        data[key] = replace_in_dict(value)
                return data
            return replace_in_dict(formatted_prompt)

        else:
            raise ValueError(f"Unknown prompt version type: {type(prompt_version_obj)}")

    def _format_for_openai(self, json_schema: Dict[str, Any], schema_name: str = "ResponseModel") -> Type[BaseModel]:
        """Format response format for OpenAI/Azure OpenAI.

        OpenAI accepts Pydantic models directly. This method converts JSON Schema
        to a Pydantic model.

        Args:
            json_schema (Dict[str, Any]): JSON Schema to convert.
            schema_name (str): Name for the generated Pydantic model.

        Returns:
            Type[BaseModel]: Pydantic model class for OpenAI.
        """
        # Extract schema if nested in json_schema structure
        if "json_schema" in json_schema and "schema" in json_schema["json_schema"]:
            schema = json_schema["json_schema"]["schema"]
            if "name" in json_schema["json_schema"]:
                schema_name = json_schema["json_schema"]["name"]
        elif "schema" in json_schema:
            schema = json_schema["schema"]
        else:
            schema = json_schema

        return self._json_schema_to_pydantic(schema, schema_name)

    def _format_for_anthropic(self, json_schema: Dict[str, Any], schema_name: str = "response") -> Dict[str, Any]:
        """Format response format for Anthropic Claude.

        Anthropic uses JSON Schema in tool definitions with tool_choice.

        Args:
            json_schema (Dict[str, Any]): JSON Schema to format.
            schema_name (str): Name for the tool function.

        Returns:
            Dict[str, Any]: Tool definition format for Anthropic.
        """
        # Extract schema if nested
        if "json_schema" in json_schema and "schema" in json_schema["json_schema"]:
            schema = json_schema["json_schema"]["schema"]
            if "name" in json_schema["json_schema"]:
                schema_name = json_schema["json_schema"]["name"]
        elif "schema" in json_schema:
            schema = json_schema["schema"]
        else:
            schema = json_schema

        return {
            "tools": [
                {
                    "type": "function",
                    "name": schema_name,
                    "input_schema": schema
                }
            ],
            "tool_choice": {
                "type": "tool",
                "name": schema_name
            }
        }

    def _format_for_google(self, json_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Format response format for Google Gemini.

        Google Gemini uses JSON Schema via responseSchema parameter.
        Uses OpenAPI 3.0 Schema subset.

        Args:
            json_schema (Dict[str, Any]): JSON Schema to format.

        Returns:
            Dict[str, Any]: responseSchema format for Google Gemini.
        """
        # Extract schema if nested
        if "json_schema" in json_schema and "schema" in json_schema["json_schema"]:
            schema = json_schema["json_schema"]["schema"]
        elif "schema" in json_schema:
            schema = json_schema["schema"]
        else:
            schema = json_schema

        # Google Gemini expects OpenAPI 3.0 Schema format
        # For most cases, the JSON Schema is compatible
        return {
            "responseSchema": schema
        }

    def _format_for_cohere(self, json_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Format response format for Cohere.

        Cohere uses JSON Schema via response_format parameter.

        Args:
            json_schema (Dict[str, Any]): JSON Schema to format.

        Returns:
            Dict[str, Any]: response_format format for Cohere.
        """
        # Extract schema if nested
        if "json_schema" in json_schema and "schema" in json_schema["json_schema"]:
            schema = json_schema["json_schema"]["schema"]
        elif "schema" in json_schema:
            schema = json_schema["schema"]
        else:
            schema = json_schema

        return {
            "response_format": schema
        }

    def format_response_format_for_provider(
        self,
        prompt_parent_id: str,
        prompt_id: str,
        version: str,
        llm: Optional[BaseChatModel],
        variables: Optional[Dict[str, Union[str, int, float, List]]] = None
    ) -> Optional[Union[Dict[str, Any], Type[BaseModel]]]:
        """Format response format schema for a specific LLM provider.

        This method detects the provider from the LLM instance and returns
        the response format in the appropriate format for that provider.

        Args:
            prompt_parent_id (str): Name of the wrapper containing the prompt.
            prompt_id (str): ID of the prompt to format.
            version (str): Version of the prompt to format.
            llm (Optional[BaseChatModel]): LLM instance to detect provider from.
            variables (Optional[Dict[str, Union[str, int, float, List]]]): Values to
                substitute in the schema. If None, uses defaults from JSON.

        Returns:
            Optional[Union[Dict[str, Any], Type[BaseModel]]]:
                Provider-specific format:
                - OpenAI: Pydantic model class
                - Anthropic: Tool definition dict
                - Google: responseSchema dict
                - Cohere: response_format dict
                - None/Unknown: JSON Schema dict (fallback)

        Example:
            >>> template = PromptTemplate("prompts.json")
            >>> llm = ChatOpenAI()
            >>> formatted = template.format_response_format_for_provider(
            ...     prompt_parent_id="addition_prompts",
            ...     prompt_id="add_numbers_text",
            ...     version="1.0",
            ...     llm=llm
            ... )
            >>> # Returns Pydantic model for OpenAI
        """
        # First, get the formatted JSON Schema
        json_schema = self.format_response_format(prompt_parent_id, prompt_id, version, variables)
        if json_schema is None:
            return None

        # Detect provider
        provider = self._detect_provider(llm)
        if provider is None:
            # Fallback to JSON Schema if provider cannot be detected
            return json_schema

        # Get schema name if available
        schema_name = "ResponseModel"
        if "json_schema" in json_schema and "name" in json_schema["json_schema"]:
            schema_name = json_schema["json_schema"]["name"]

        # Format based on provider
        try:
            if provider == "openai":
                return self._format_for_openai(json_schema, schema_name)
            elif provider == "anthropic":
                return self._format_for_anthropic(json_schema, schema_name)
            elif provider == "google":
                return self._format_for_google(json_schema)
            elif provider == "cohere":
                return self._format_for_cohere(json_schema)
            else:
                # Unknown provider, return JSON Schema as fallback
                return json_schema
        except (ValueError, KeyError) as e:
            # If conversion fails, return original JSON Schema
            # This maintains backward compatibility
            return json_schema

    def format_response_format(
        self,
        prompt_parent_id: str,
        prompt_id: str,
        version: str,
        variables: Optional[Dict[str, Union[str, int, float, List]]] = None
    ) -> Optional[Dict]:
        """Format the response format schema by replacing variables with values.

        This method specifically handles variable substitution in response format schemas,
        including enum values in JSON schemas.

        Args:
            prompt_parent_id (str): Name of the wrapper containing the prompt.
            prompt_id (str): ID of the prompt to format.
            version (str): Version of the prompt to format.
            variables (Optional[Dict[str, Union[str, int, float, List]]]): Values to
                substitute in the schema. If None, uses defaults from JSON.

        Returns:
            Optional[Dict]: Formatted response format schema if found and successfully
                formatted, None otherwise.

        Example:
            >>> template = PromptTemplate("prompts.json")
            >>> formatted_schema = template.format_response_format(
            ...     prompt_parent_id="supplement",
            ...     prompt_id="recommendation",
            ...     version="1.0",
            ...     variables={"available_skus": ["SKU-001", "SKU-002", "SKU-003"]}
            ... )
        """
        prompt_version_obj = self.get_prompt_version(prompt_parent_id, prompt_id, version)

        if not prompt_version_obj:
            return None

        prompt_variables = prompt_version_obj.variables or {}
        final_variables = prompt_variables.copy()

        if variables:
            final_variables.update(variables)

        if not prompt_version_obj.response_format:
            return None

        formatted_response_format = copy.deepcopy(prompt_version_obj.response_format)

        def replace_in_schema(data: Any) -> Any:
            """Recursively replace variables in schema data.

            Args:
                data (Any): Data to process (dict, list, or primitive).

            Returns:
                Any: Data with variables replaced.
            """
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, str):
                        for var_name, var_value in final_variables.items():
                            placeholder = f"{{{var_name}}}"
                            if placeholder in value:
                                data[key] = value.replace(placeholder, str(var_value))
                    elif isinstance(value, list):
                        data[key] = replace_in_schema(value)
                    elif isinstance(value, dict):
                        data[key] = replace_in_schema(value)
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    if isinstance(item, str):
                        for var_name, var_value in final_variables.items():
                            if item == f"{{{var_name}}}":
                                if isinstance(var_value, list):
                                    data[i:i+1] = var_value
                                    return data
                                else:
                                    data[i] = var_value
                    else:
                        data[i] = replace_in_schema(item)
            return data

        return replace_in_schema(formatted_response_format)

    def get_full_formatted_prompt(
        self,
        prompt_parent_id: str,
        prompt_id: str,
        version: str,
        variables: Optional[Dict[str, Union[str, int, float, List]]] = None,
        llm: Optional[BaseChatModel] = None
    ) -> Optional[Dict[str, Union[str, List[Dict[str, str]], Dict, Type[BaseModel]]]]:
        """Get a formatted prompt with metadata.

        This method formats a prompt and returns it along with its description
        and output schema. It's useful when you need the complete prompt
        context, not just the formatted content.

        Args:
            prompt_parent_id (str): Name of the wrapper containing the prompt.
            prompt_id (str): ID of the prompt to format.
            version (str): Version of the prompt to format.
            variables (Optional[Dict[str, Union[str, int, float, List]]]): Values to
                substitute in the prompt. If None, uses defaults from JSON.
            llm (Optional[BaseChatModel]): Optional LLM instance for provider-specific
                schema formatting. If provided, output_schema will be formatted for
                the detected provider.

        Returns:
            Optional[Dict[str, Union[str, List[Dict[str, str]], Dict, Type[BaseModel]]]]:
                Dictionary containing formatted content, description, and schema,
                or None if prompt not found. The output_schema will be provider-specific
                if llm is provided, otherwise it will be JSON Schema.

        Example:
            >>> template = PromptTemplate("prompts.json")
            >>> result = template.get_full_formatted_prompt(
            ...     prompt_parent_id="text",
            ...     prompt_id="search",
            ...     version="1.0",
            ...     variables={"query": "python"}
            ... )
            >>> print(result["description"])
            'Search query template'
            >>> # With provider-specific formatting:
            >>> llm = ChatOpenAI()
            >>> result = template.get_full_formatted_prompt(
            ...     prompt_parent_id="addition_prompts",
            ...     prompt_id="add_numbers_text",
            ...     version="1.0",
            ...     llm=llm
            ... )
            >>> # output_schema will be a Pydantic model for OpenAI
        """
        target_prompt = None
        for pg in self.prompts:
            if pg.prompt_parent_id == prompt_parent_id:
                for p in pg.prompts:
                    if p.prompt_id == prompt_id:
                        target_prompt = p
                        break
                if target_prompt:
                    break

        if not target_prompt:
            return None

        prompt_version_obj = self.get_prompt_version(prompt_parent_id, prompt_id, version)

        if not prompt_version_obj:
            return None

        formatted_content = self.format_prompt(prompt_parent_id, prompt_id, version, variables)
        if not formatted_content:
            return None

        # Format the response format schema
        # Use provider-specific formatting if llm is provided
        if llm is not None:
            formatted_response_format = self.format_response_format_for_provider(
                prompt_parent_id, prompt_id, version, llm, variables
            )
        else:
            formatted_response_format = self.format_response_format(
                prompt_parent_id, prompt_id, version, variables
            )

        return {
            "description": target_prompt.description,
            "content": formatted_content,
            "output_schema": formatted_response_format
        }
