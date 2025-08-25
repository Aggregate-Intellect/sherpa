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

from sherpa_ai.prompts.Base import (
    ChatPromptVersion,
    Prompt,
    PromptGroup,
    TextPromptVersion,
    JsonPromptVersion,
    PromptVersion
)

PROMPTS_ATTR = "prompts"
CONTENT_ATTR = "content"
RESPONSE_FORMAT_ATTR = "response_format"
TYPE_ATTR = "type"
PROMPT_PARENT_ID_ATTR = "prompt_parent_id"
PROMPT_ID_ATTR = "prompt_id"
VERSIONS_ATTR = "versions"
VERSION_ATTR = "version"


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
            json_data (Union[str, dict, list]): JSON string, dictionary, or list to convert.
        """
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data

        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    value = JsonToObject(value)
                elif isinstance(value, list):
                    value = [JsonToObject(item) if isinstance(item, dict) else item for item in value]
                setattr(self, key, value)
        elif isinstance(data, list):
            self._list_data = [JsonToObject(item) if isinstance(item, dict) else item for item in data]
        else:
            self._value = data


    def __repr__(self):
        if hasattr(self, '_list_data'):
            return f"{self._list_data}"
        elif hasattr(self, '_value'):
            return f"{self._value}"
        return f"{self.__dict__}"

    def __iter__(self):
        if hasattr(self, '_list_data'):
            return iter(self._list_data)
        raise TypeError("JsonToObject is not iterable unless initialized with a list root.")

    def __getitem__(self, key):
        if hasattr(self, '_list_data'):
            return self._list_data[key]
        raise TypeError("JsonToObject does not support indexing unless initialized with a list root.")


def load_json(file_path: str) -> Union[Dict, List]:
    """Load JSON data from a file path or package resource.

    This function attempts to load JSON data first from the package resources,
    then from the filesystem if not found in resources.

    Args:
        file_path (str): Path to JSON file (relative to sherpa_ai or absolute).

    Returns:
        Union[Dict, List]: Loaded JSON data as a dictionary or list.

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
            with resource_path.open('r', encoding='utf-8') as f:
                return json.load(f)
        
        # If not found as resource, try as filesystem path
        abs_path = Path(file_path).resolve()
        if abs_path.exists():
            with abs_path.open('r', encoding='utf-8') as f:
                return json.load(f)
                
        raise FileNotFoundError(f"File not found at either resource path: {clean_path} or absolute path: {abs_path}")
        
    except FileNotFoundError as e:
        raise FileNotFoundError(f"File not found: {file_path}") from e


def get_prompts(data: Union[Dict, List]) -> Dict[str, List[Dict]]:
    """Extract prompts from loaded JSON data.

    This function processes the JSON data structure to extract all prompts,
    organizing them by their wrapper names.

    Args:
        data (Union[Dict, List]): JSON data containing prompt definitions.

    Returns:
        Dict[str, List[Dict]]: Dictionary mapping wrapper names to prompt lists.

    Example:
        >>> data = {"wrapper1": [{"prompts": [{"name": "p1"}, {"name": "p2"}]}]}
        >>> prompts = get_prompts(data)
        >>> print(len(prompts["wrapper1"]))
        2
    """
    all_prompts = {}
    if isinstance(data, list):
        for item_data in data:
            wrapper_name = item_data.get(PROMPT_PARENT_ID_ATTR)
            if wrapper_name:
                prompts = item_data.get(PROMPTS_ATTR, [])
                all_prompts[wrapper_name] = prompts
    elif isinstance(data, dict):
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
        data (Union[Dict, List]): Raw JSON data.
        prompts (List[PromptGroup]): Validated prompt groups.

    Example:
        >>> loader = PromptLoader("prompts.json")
        >>> prompt = loader.get_prompt("prompt_parent_id", "prompt_id", "1.0")
        >>> print(prompt.content)
        'Hello {name}!'
    """

    def __init__(self, json_file_path: str):
        """Initialize the prompt loader.

        Args:
            json_file_path (str): Path to JSON file containing prompts.
        """
        raw_data = load_json(json_file_path)
        self.data = raw_data
        self.prompts = self._process_prompts()

    def _validate_prompt_version_structure(self, version_data: Dict) -> bool:
        """Validate the structure and types of a single prompt version.
        This method checks that a prompt dictionary has all required fields
        with correct types.
        Args:
            version_data (Dict): Dictionary representing a prompt version.

        Returns:
            bool: True if validation passes.

        Raises:
            InvalidPromptContentError: If validation fails.
        """
        required_attrs = {
            VERSION_ATTR: str,
            "change_log": str,
            TYPE_ATTR: str,
            CONTENT_ATTR: (str, list, dict),
            "variables": dict,
            RESPONSE_FORMAT_ATTR: dict,
        }

        for attr, expected_type in required_attrs.items():
            if attr not in version_data:
                raise InvalidPromptContentError(f"Prompt version must have '{attr}' attribute.")
            if not isinstance(version_data[attr], expected_type):
                raise InvalidPromptContentError(
                    f"'{attr}' must be of type {expected_type} for version '{version_data.get(VERSION_ATTR, 'Unknown')}'. "
                    f"Found '{type(version_data[attr]).__name__}'."
                )

        content_type = version_data.get(TYPE_ATTR)
        content = version_data.get(CONTENT_ATTR)

        if content_type == "text" and not (isinstance(content, str) or isinstance(content, list)):
            raise InvalidPromptContentError("'content' must be a string or list of strings when 'type' is 'text'.")
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
        validated_prompt_groups = []
        for prompt_group_data in self.data:
            try:
                if not isinstance(prompt_group_data, dict):
                    raise InvalidPromptContentError(
                        f"Expected a dictionary for prompt group, but got {type(prompt_group_data).__name__}."
                    )

                processed_prompts = []
                for prompt_data in prompt_group_data.get(PROMPTS_ATTR, []):
                    # Validate prompt_id and description for the Prompt itself
                    if PROMPT_ID_ATTR not in prompt_data or not isinstance(prompt_data[PROMPT_ID_ATTR], str):
                        raise InvalidPromptContentError(f"Prompt must have a string '{PROMPT_ID_ATTR}' attribute.")
                    if "description" not in prompt_data or not isinstance(prompt_data["description"], str):
                        raise InvalidPromptContentError(f"Prompt '{prompt_data.get(PROMPT_ID_ATTR, 'Unknown')}' must have a string 'description' attribute.")


                    processed_versions = []
                    if VERSIONS_ATTR not in prompt_data or not isinstance(prompt_data[VERSIONS_ATTR], list):
                        raise InvalidPromptContentError(
                            f"Prompt '{prompt_data.get(PROMPT_ID_ATTR, 'Unknown')}' must have a list '{VERSIONS_ATTR}' attribute."
                        )

                    for version_data in prompt_data[VERSIONS_ATTR]:
                        self._validate_prompt_version_structure(version_data)
                        content_type = version_data.get(TYPE_ATTR)

                        if content_type == "chat":
                            prompt_version = ChatPromptVersion(**version_data)
                        elif content_type == "text":
                            prompt_version = TextPromptVersion(**version_data)
                        elif content_type == "json":
                            prompt_version = JsonPromptVersion(**version_data)
                        else:
                            raise InvalidPromptContentError(f"Unknown 'type': {content_type} in prompt version.")
                        processed_versions.append(prompt_version)

                    prompt_obj = Prompt(
                        prompt_id=prompt_data[PROMPT_ID_ATTR],
                        description=prompt_data["description"],
                        versions=processed_versions
                    )
                    processed_prompts.append(prompt_obj)

                prompt_group_obj = PromptGroup(
                    prompt_parent_id=prompt_group_data[PROMPT_PARENT_ID_ATTR],
                    description=prompt_group_data["description"],
                    prompts=processed_prompts
                )
                validated_prompt_groups.append(prompt_group_obj)

            except ValidationError as e:
                error_details = [
                    f"Field '{'.'.join(str(loc) for loc in err['loc'])}': {err['msg']}"
                    for err in e.errors()
                ]
                raise InvalidPromptContentError(
                    f"Validation failed for prompt group: {', '.join(error_details)}"
                ) from e
            except KeyError as e:
                raise InvalidPromptContentError(f"Missing expected key in prompt group data: {e}") from e

        return validated_prompt_groups

    def get_prompt_version(self, prompt_parent_id: str, prompt_id: str, version: str) -> Optional[PromptVersion]:
        """Get a specific prompt version by its identifiers.

        Args:
            prompt_parent_id (str): Prompt group ID.
            prompt_id (str): Unique identifier for the prompt.
            version (str): Specific version of the prompt.

        Returns:
            Optional[PromptVersion]: The requested prompt version if found, None otherwise.
        """
        for prompt_group in self.prompts:
            if prompt_group.prompt_parent_id == prompt_parent_id:
                for prompt in prompt_group.prompts:
                    if prompt.prompt_id == prompt_id:
                        for prompt_version in prompt.versions:
                            if prompt_version.version == version:
                                return prompt_version
        return None

    def get_prompt_content(self, prompt_parent_id: str, prompt_id: str, version: str) -> Optional[Any]:
        """Get the content of a specific prompt version.

        Args:
            prompt_parent_id (str): Prompt group ID.
            prompt_id (str): Unique identifier for the prompt.
            version (str): Specific version of the prompt.

        Returns:
            Optional[Any]: The prompt version's content if found, None otherwise.
        """
        prompt_version = self.get_prompt_version(prompt_parent_id, prompt_id, version)
        if prompt_version:
            return prompt_version.content
        return None

    def get_prompt_output_schema(self, prompt_parent_id: str, prompt_id: str, version: str) -> Optional[Dict]:
        """Get the output schema of a specific prompt version.

        Args:
            prompt_parent_id (str): Prompt group ID.
            prompt_id (str): Unique identifier for the prompt.
            version (str): Specific version of the prompt.

        Returns:
            Optional[Dict]: The prompt version's response format (output schema) if found, None otherwise.
        Example:
            >>> content = loader.get_prompt_content("chat", "greeting", "1.0")
            >>> print(content)
            'Hello {name}!'
        """
        prompt_version = self.get_prompt_version(prompt_parent_id, prompt_id, version)
        if prompt_version and hasattr(prompt_version, RESPONSE_FORMAT_ATTR):
            return prompt_version.response_format
        return None