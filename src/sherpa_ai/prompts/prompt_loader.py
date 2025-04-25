"""Prompt loading and validation module for Sherpa AI.

This module provides functionality for loading and validating prompts from
JSON files. It includes classes and functions for converting JSON data into
prompt objects, validating their structure, and managing prompt collections.
"""

from importlib import resources
from typing import Dict, List, Optional, Any, Union
import json
from pydantic import ValidationError
from pathlib import Path

from sherpa_ai.prompts.Base import ChatPrompt, Prompt, PromptGroup, TextPrompt, JsonPrompt

PROMPTS_ATTR = "prompts"
CONTENT_ATTR = "content"
RESPONSE_FORMAT_ATTR = "response_format"
TYPE_ATTR = "type"


class JsonToObject:
    """Utility class for converting JSON data to Python objects.

    This class recursively converts JSON data into Python objects with
    attributes matching the JSON structure.

    Example:
        >>> data = {"name": "test", "config": {"value": 42}}
        >>> obj = JsonToObject(data)
        >>> print(obj.name)
        'test'
        >>> print(obj.config.value)
        42
    """
    def __init__(self, json_data):
        """Initialize from JSON data.

        Args:
            json_data (Union[str, dict]): JSON string or dictionary to convert.
        """
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data
            
        for key, value in data.items():
            if isinstance(value, dict):
                value = JsonToObject(value)
            elif isinstance(value, list):
                value = [JsonToObject(item) if isinstance(item, dict) else item for item in value]
            setattr(self, key, value)
        
    def __repr__(self):
        return f"{self.__dict__}"


def load_json(file_path: str) -> Dict:
    """Load JSON data from a file path or package resource.
    
    This function attempts to load JSON data first from the package resources,
    then from the filesystem if not found in resources.
    
    Args:
        file_path (str): Path to JSON file (relative to sherpa_ai or absolute).

    Returns:
        Dict: Loaded JSON data as a dictionary.

    Raises:
        FileNotFoundError: If file not found in resources or filesystem.

    Example:
        >>> data = load_json("prompts/templates.json")
        >>> print(data["version"])
        '1.0'
    """
    try:
        # First try to load as a package resource
        clean_path = file_path.replace('sherpa_ai/', '').strip('./')
        resource_path = resources.files("sherpa_ai").joinpath(clean_path)
        
        if resource_path.exists():  # Check if resource exists
            with resource_path.open('r') as f:
                return json.load(f)
        
        # If not found as resource, try as filesystem path
        abs_path = Path(file_path).resolve()
        if abs_path.exists():
            with abs_path.open('r') as f:
                return json.load(f)
                
        raise FileNotFoundError(f"File not found at either resource path: {clean_path} or absolute path: {abs_path}")
        
    except FileNotFoundError as e:
        raise FileNotFoundError(f"File not found: {file_path}") from e


def get_prompts(data: Dict) -> Dict[str, List[Dict]]:
    """Extract prompts from loaded JSON data.

    This function processes the JSON data structure to extract all prompts,
    organizing them by their wrapper names.

    Args:
        data (Dict): JSON data containing prompt definitions.

    Returns:
        Dict[str, List[Dict]]: Dictionary mapping wrapper names to prompt lists.

    Example:
        >>> data = {"wrapper1": [{"prompts": [{"name": "p1"}, {"name": "p2"}]}]}
        >>> prompts = get_prompts(data)
        >>> print(len(prompts["wrapper1"]))
        2
    """
    all_prompts = {}
    for wrapper, items in data.items():
        all_prompts[wrapper] = []
        for item in items:
            prompts = item.get(PROMPTS_ATTR, [])
            all_prompts[wrapper].extend(prompts)
    return all_prompts


class InvalidPromptContentError(Exception):
    """Exception for invalid prompt content.

    This exception is raised when prompt content doesn't match the expected
    structure or types.

    Example:
        >>> try:
        ...     raise InvalidPromptContentError("Missing 'content' field")
        ... except InvalidPromptContentError as e:
        ...     print(str(e))
        'Missing 'content' field'
    """
    pass


class PromptLoader:
    """Loader class for managing prompt collections.

    This class handles loading prompts from JSON files, validating their
    structure, and providing access to individual prompts.

    Attributes:
        data (JsonToObject): Raw JSON data converted to objects.
        prompts (List[PromptGroup]): Validated prompt groups.

    Example:
        >>> loader = PromptLoader("prompts.json")
        >>> prompt = loader.get_prompt("wrapper", "name", "1.0")
        >>> print(prompt.content)
        'Hello {name}!'
    """

    def __init__(self, json_file_path: str):
        """Initialize the prompt loader.

        Args:
            json_file_path (str): Path to JSON file containing prompts.
        """
        raw_data = load_json(json_file_path)
        self.data = JsonToObject(raw_data)
        self.prompts = self._process_prompts()

    def _validate_prompt_structure(self, prompt: Dict) -> bool:
        """Validate prompt structure and types.

        This method checks that a prompt dictionary has all required fields
        with correct types.

        Args:
            prompt (Dict): Prompt dictionary to validate.

        Returns:
            bool: True if validation passes.

        Raises:
            InvalidPromptContentError: If validation fails.
        """
        required_attrs = {
            "name": str,
            "version": str,
            "type": str,
            "content": (str, list, dict),
        }

        for attr, expected_type in required_attrs.items():
            if attr not in prompt:
                raise InvalidPromptContentError(f"Prompt must have '{attr}' attribute.")
            if not isinstance(prompt[attr], expected_type):
                raise InvalidPromptContentError(
                    f"'{attr}' must be of type {expected_type} for prompt '{prompt.get('name', 'Unknown')}'. "
                    f"Found '{type(prompt[attr]).__name__}'."
                )

        content_type = prompt.get(TYPE_ATTR)
        content = prompt.get(CONTENT_ATTR)

        if content_type == "text" and not isinstance(content, str):
            raise InvalidPromptContentError("'content' must be a string when 'type' is 'text'.")
        elif content_type == "chat" and not isinstance(content, list):
            raise InvalidPromptContentError("'content' must be a list when 'type' is 'chat'.")
        elif content_type == "json" and not isinstance(content, dict):
            raise InvalidPromptContentError("'content' must be a dict when 'type' is 'json'.")
        return True

    def _process_prompts(self) -> List[PromptGroup]:
        """Process and validate loaded prompts.

        This method converts raw JSON data into validated prompt objects,
        organizing them into prompt groups.

        Returns:
            List[PromptGroup]: List of validated prompt groups.

        Raises:
            InvalidPromptContentError: If validation fails.
        """
        validated_prompts = []
        for wrapper, items in self.data.__dict__.items():
            for item in items:
                try:
                    item_dict = self._convert_to_dict(item)
                    processed_prompts = []

                    for prompt_data in item_dict[PROMPTS_ATTR]:
                        self._validate_prompt_structure(prompt_data)
                        content_type = prompt_data.get(TYPE_ATTR)
                        if content_type == "chat":
                            prompt = ChatPrompt(**prompt_data)
                        elif content_type == "text":
                            prompt = TextPrompt(**prompt_data)
                        elif content_type == "json":
                            prompt = JsonPrompt(**prompt_data)
                        else:
                            raise InvalidPromptContentError(f"Unknown 'type': {content_type}")
                        processed_prompts.append(prompt)

                    item_dict[PROMPTS_ATTR] = processed_prompts
                    prompt_group = PromptGroup(**item_dict)
                    validated_prompts.append(prompt_group)

                except ValidationError as e:
                    error_details = [
                        f"Field '{'.'.join(str(loc) for loc in err['loc'])}': {err['msg']}"
                        for err in e.errors()
                    ]
                    raise InvalidPromptContentError(
                        f"Validation failed for prompts in '{wrapper}': {', '.join(error_details)}"
                    ) from e

        return validated_prompts

    def _convert_to_dict(self, obj: Any) -> Any:
        """Recursively convert JsonToObject instances to dictionaries.

        Args:
            obj (Any): Object to convert.

        Returns:
            Any: Converted object (dict if input was JsonToObject).
        """
        if isinstance(obj, JsonToObject):
            return {key: self._convert_to_dict(value) for key, value in obj.__dict__.items()}
        elif isinstance(obj, list):
            return [self._convert_to_dict(item) for item in obj]
        return obj

    def get_prompt(self, wrapper: str, name: str, version: str) -> Optional[Prompt]:
        """Get a specific prompt by its identifiers.

        Args:
            wrapper (str): Wrapper name containing the prompt.
            name (str): Name of the prompt.
            version (str): Version of the prompt.

        Returns:
            Optional[Prompt]: The requested prompt if found, None otherwise.

        Example:
            >>> prompt = loader.get_prompt("chat", "greeting", "1.0")
            >>> if prompt:
            ...     print(prompt.content)
            'Hello {name}!'
        """
        for prompt_group in self.prompts:
            if prompt_group.name == wrapper:
                for prompt in prompt_group.prompts:
                    if prompt.name == name and prompt.version == version:
                        return prompt
        return None

    def get_prompt_content(self, wrapper: str, name: str, version: str) -> Optional[Any]:
        """Get the content of a specific prompt.

        Args:
            wrapper (str): Wrapper name containing the prompt.
            name (str): Name of the prompt.
            version (str): Version of the prompt.

        Returns:
            Optional[Any]: The prompt content if found, None otherwise.

        Example:
            >>> content = loader.get_prompt_content("chat", "greeting", "1.0")
            >>> print(content)
            'Hello {name}!'
        """
        prompt = self.get_prompt(wrapper, name, version)
        if prompt:
            return prompt.content
        return None

    def get_prompt_output_schema(self, wrapper: str, name: str, version: str) -> Optional[Any]:
        """Get the output schema of a specific prompt.

        Args:
            wrapper (str): Wrapper name containing the prompt.
            name (str): Name of the prompt.
            version (str): Version of the prompt.

        Returns:
            Optional[Any]: The prompt's output schema if found, None otherwise.

        Example:
            >>> schema = loader.get_prompt_output_schema("chat", "greeting", "1.0")
            >>> print(schema["type"])
            'string'
        """
        prompt = self.get_prompt(wrapper, name, version)
        if prompt and hasattr(prompt, RESPONSE_FORMAT_ATTR):
            return prompt.response_format
        return None
