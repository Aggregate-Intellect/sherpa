from importlib import resources
from typing import Dict, List, Optional, Any, Union
import json
from pydantic import ValidationError
from pathlib import Path

from sherpa_ai.prompts.Base import ChatPrompt, Prompt, PromptGroup, TextPrompt,JsonPrompt

PROMPTS_ATTR = "prompts"
CONTENT_ATTR = "content"
RESPONSE_FORMAT_ATTR = "response_format"
TYPE_ATTR = "type"


class JsonToObject:
    def __init__(self, json_data):
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
    """
    Load JSON data from either a package resource or a filesystem path.
    
    Args:
        file_path: Path to JSON file (can be relative to sherpa_ai package or absolute)
    Returns:
        Dict containing the JSON data
    Raises:
        FileNotFoundError: If the file cannot be found
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
    """
    Extract prompts from the loaded JSON data.
    """
    all_prompts = {}
    for wrapper, items in data.items():
        all_prompts[wrapper] = []
        for item in items:
            prompts = item.get(PROMPTS_ATTR, [])
            all_prompts[wrapper].extend(prompts)
    return all_prompts


class InvalidPromptContentError(Exception):
    """Raised when prompt content doesn't match expected structure."""
    pass


class PromptLoader:
    def __init__(self, json_file_path: str):
        raw_data = load_json(json_file_path)
        self.data = JsonToObject(raw_data)
        self.prompts = self._process_prompts()

    def _validate_prompt_structure(self, prompt: Dict) -> bool:
        """
        Validate that the prompt has the required structure and types.
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
        """
        Process the loaded data and validate against Pydantic models.
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
        """
        Recursively convert JsonToObject instances to dictionaries.
        """
        if isinstance(obj, JsonToObject):
            return {key: self._convert_to_dict(value) for key, value in obj.__dict__.items()}
        elif isinstance(obj, list):
            return [self._convert_to_dict(item) for item in obj]
        return obj

    def get_prompt(self, wrapper: str, name: str, version: str) -> Optional[Prompt]:
        """
        Get a specific prompt by wrapper, name, and version.
        """
        for prompt_group in self.prompts:
            if prompt_group.name == wrapper:
                for prompt in prompt_group.prompts:
                    if prompt.name == name and prompt.version == version:
                        return prompt
        return None

    def get_prompt_content(self, wrapper: str, name: str, version: str) -> Optional[Any]:
        """
        Get the content of a specific prompt by wrapper, name, and version.
        """
        prompt = self.get_prompt(wrapper, name, version)
        if prompt:
            return prompt.content
        return None

    def get_prompt_output_schema(self, wrapper: str, name: str, version: str) -> Optional[Any]:
        """
        Get the output schema of a specific prompt by wrapper, name, and version.
        """
        prompt = self.get_prompt(wrapper, name, version)
        if prompt and hasattr(prompt, RESPONSE_FORMAT_ATTR):
            return prompt.response_format
        return None
