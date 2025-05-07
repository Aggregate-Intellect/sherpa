"""Prompt template loading and formatting module for Sherpa AI.

This module provides functionality for loading prompt templates and formatting
them with variables. It extends the base PromptLoader to add variable
substitution capabilities for different prompt types.
"""

import json
from typing import Dict, List, Optional, Union
from sherpa_ai.prompts.Base import ChatPrompt, TextPrompt, JsonPrompt
from sherpa_ai.prompts.prompt_loader import PromptLoader

class PromptTemplate(PromptLoader):
    """Template loader and formatter for prompts.

    This class extends PromptLoader to add variable substitution capabilities.
    It can format text, chat, and JSON prompts by replacing placeholders
    with actual values.

    Example:
        >>> template = PromptTemplate("prompts.json")
        >>> formatted = template.format_prompt(
        ...     wrapper="chat",
        ...     name="greeting",
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
        wrapper: str,
        name: str,
        version: str,
        variables: Optional[Dict[str, Union[str, int, float]]] = None
    ) -> Optional[Union[str, List[Dict[str, str]], Dict]]:
        """Format a prompt by replacing variables with values.

        This method loads a prompt template and replaces any variable
        placeholders with provided values. It handles different prompt types
        (text, chat, JSON) appropriately.

        Args:
            wrapper (str): Name of the wrapper containing the prompt.
            name (str): Name of the prompt to format.
            version (str): Version of the prompt to format.
            variables (Optional[Dict[str, Union[str, int, float]]]): Values to
                substitute in the prompt. If None, uses defaults from JSON.

        Returns:
            Optional[Union[str, List[Dict[str, str]], Dict]]: Formatted prompt
                content if found and successfully formatted, None otherwise.

        Example:
            >>> template = PromptTemplate("prompts.json")
            >>> formatted = template.format_prompt(
            ...     wrapper="text",
            ...     name="search",
            ...     version="1.0",
            ...     variables={"query": "python programming"}
            ... )
            >>> print(formatted)
            'Search for: python programming'
        """
        prompt = None
        for pg in self.prompts:
            if pg.name == wrapper:
                for p in pg.prompts:
                    if p.name == name and p.version == version:
                        # Convert the prompt to appropriate type based on content
                        if isinstance(p.content, list):
                            prompt = ChatPrompt(
                                name=p.name,
                                description=p.description,
                                version=p.version,
                                content=p.content,
                                variables=p.variables,
                                response_format=p.response_format
                            )
                        elif isinstance(p.content, str):
                            prompt = TextPrompt(
                                name=p.name,
                                description=p.description,
                                version=p.version,
                                content=p.content,
                                variables=p.variables,
                                response_format=p.response_format
                            )
                        elif isinstance(p.content, dict):
                            prompt = JsonPrompt(
                                name=p.name,
                                description=p.description,
                                version=p.version,
                                content=p.content,
                                variables=p.variables,
                                response_format=p.response_format
                            )
                        break
                break
        
        if not prompt:
            return None

        prompt_variables = prompt.variables or {}
        final_variables = prompt_variables.copy()

        if variables:
            final_variables.update(variables)

        if isinstance(prompt, ChatPrompt):
            formatted_prompt = []
            for message in prompt.content:
                role = message.get("role")
                text = message.get("content", "")

                # Replace placeholders with variables
                for var_name, var_value in final_variables.items():
                    placeholder = f"{{{var_name}}}"
                    if placeholder in text:
                        text = text.replace(placeholder, str(var_value))

                formatted_prompt.append({"role": role, "content": text})
            return formatted_prompt

        elif isinstance(prompt, TextPrompt):
            text = prompt.content
            for var_name, var_value in final_variables.items():
                placeholder = f"{{{var_name}}}"
                if placeholder in text:
                    text = text.replace(placeholder, str(var_value))
            return text

        elif isinstance(prompt, JsonPrompt):
            import copy
            formatted_prompt = copy.deepcopy(prompt.content) 
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
            raise ValueError(f"Unknown prompt type: {type(prompt)}")

    def get_full_formatted_prompt(
        self,
        wrapper: str,
        name: str,
        version: str,
        variables: Optional[Dict[str, Union[str, int, float]]] = None
    ) -> Optional[Dict[str, Union[str, List[Dict[str, str]], Dict]]]:
        """Get a formatted prompt with metadata.

        This method formats a prompt and returns it along with its description
        and output schema. It's useful when you need the complete prompt
        context, not just the formatted content.

        Args:
            wrapper (str): Name of the wrapper containing the prompt.
            name (str): Name of the prompt to format.
            version (str): Version of the prompt to format.
            variables (Optional[Dict[str, Union[str, int, float]]]): Values to
                substitute in the prompt. If None, uses defaults from JSON.

        Returns:
            Optional[Dict[str, Union[str, List[Dict[str, str]], Dict]]]:
                Dictionary containing formatted content, description, and schema,
                or None if prompt not found.

        Example:
            >>> template = PromptTemplate("prompts.json")
            >>> result = template.get_full_formatted_prompt(
            ...     wrapper="text",
            ...     name="search",
            ...     version="1.0",
            ...     variables={"query": "python"}
            ... )
            >>> print(result["description"])
            'Search query template'
        """
        prompt = None
        for pg in self.prompts:
            if pg.name == wrapper:
                for p in pg.prompts:
                    if p.name == name and p.version == version:
                        # Convert the prompt to appropriate type
                        if isinstance(p.content, list):
                            prompt = ChatPrompt(
                                name=p.name,
                                description=p.description,
                                version=p.version,
                                content=p.content,
                                variables=p.variables,
                                response_format=p.response_format
                            )
                        elif isinstance(p.content, str):
                            prompt = TextPrompt(
                                name=p.name,
                                description=p.description,
                                version=p.version,
                                content=p.content,
                                variables=p.variables,
                                response_format=p.response_format
                            )
                        elif isinstance(p.content, dict):
                            prompt = JsonPrompt( 
                                name=p.name,
                                description=p.description,
                                version=p.version,
                                content=p.content,
                                variables=p.variables,
                                response_format=p.response_format
                            )
                        break
                break
        
        if not prompt:
            return None

        formatted_content = self.format_prompt(wrapper, name, version, variables)
        if not formatted_content:
            return None

        return {
            "description": prompt.description,
            "content": formatted_content,
            "output_schema": prompt.response_format
        }