"""Prompt template loading and formatting module for Sherpa AI.

This module provides functionality for loading prompt templates and formatting
them with variables. It extends the base PromptLoader to add variable
substitution capabilities for different prompt types.
"""

from typing import Dict, List, Optional, Union, Any
from sherpa_ai.prompts.Base import ChatPromptVersion, TextPromptVersion, JsonPromptVersion
from sherpa_ai.prompts.prompt_loader import PromptLoader
import copy

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
        variables: Optional[Dict[str, Union[str, int, float, List]]] = None
    ) -> Optional[Dict[str, Union[str, List[Dict[str, str]], Dict]]]:
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

        Returns:
            Optional[Dict[str, Union[str, List[Dict[str, str]], Dict]]]:
                Dictionary containing formatted content, description, and schema,
                or None if prompt not found.

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

        # Format the response format schema as well
        formatted_response_format = self.format_response_format(
            prompt_parent_id, prompt_id, version, variables
        )

        return {
            "description": target_prompt.description,
            "content": formatted_content,
            "output_schema": formatted_response_format
        }
