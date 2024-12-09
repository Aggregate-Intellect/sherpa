from typing import Dict, List, Optional, Union, Any
import json

from pydantic import ValidationError

from sherpa_ai.prompts.Base import ChatPrompt, Prompt, PromptGroup, TextPrompt


PROMPTS_ATTR = "prompts"
CONTENT_ATTR = "content"
RESPONSE_FORMAT_ATTR = "response_format"
TYPE_ATTR = "type"


import json
from typing import Dict, List

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
    Load JSON data from a file.
    
    Args:
        file_path (str): Path to the JSON file.
    
    Returns:
        Dict: Loaded JSON data.
    """
    with open(file_path, 'r') as file:
        return json.load(file)

def get_prompts(data: Dict) -> Dict[str, List[Dict]]:
    """
    Extract prompts from the loaded JSON data.
    
    Args:
        data (Dict): Loaded JSON data.
    
    Returns:
        Dict[str, List[Dict]]: Dictionary of all prompts grouped by their wrapper.
    """
    all_prompts = {}
    for wrapper, items in data.items():
        all_prompts[wrapper] = []
        for item in items:
            prompts = item.get(PROMPTS_ATTR, [])
            all_prompts[wrapper].extend(prompts)
    return all_prompts

class InvalidPromptContentError(Exception):
    """Raised when prompt content doesn't match expected structure"""
    pass

class PromptLoader:
    def __init__(self, json_file_path: str):
        raw_data = load_json(json_file_path)
        self.data = JsonToObject(raw_data)
        self.prompts = self._process_prompts()


    def _validate_prompt_structure(self, prompt: Dict) -> bool:
        """ 
        Validate that the prompt has the required structure and types.
        
        Args:
            prompt (Dict): The prompt dictionary to validate.

        Raises:
            InvalidPromptContentError: If any part of the prompt structure is invalid.
        """
        required_attrs = {
            "name": str,
            "version": str,
            "type": str,
            "content": (str, list)
        }

        # Check for required attributes and validate their types
        for attr, expected_type in required_attrs.items():
            if attr not in prompt:
                raise InvalidPromptContentError(f"Prompt must have '{attr}' attribute.")
            
            # Check if the attribute matches expected type(s)
            if not isinstance(prompt[attr], expected_type):
                # If expected_type is a tuple, create a human-readable type list
                if isinstance(expected_type, tuple):
                    type_names = [t.__name__ for t in expected_type]
                    type_str = " or ".join(type_names)
                else:
                    type_str = expected_type.__name__
                
                raise InvalidPromptContentError(
                    f"Prompt '{attr}' must be of type '{type_str}' for the prompt {prompt.get('name', 'Unknown')}. "
                    f"Found '{type(prompt[attr]).__name__}' instead."
                )

        # Validate that `content` type matches `type` field specification
        content_type = prompt.get(TYPE_ATTR)
        content = prompt.get(CONTENT_ATTR)
        
        if content_type == "text" and not isinstance(content, str):
            raise InvalidPromptContentError(f"Prompt content must be a string when type is 'text' for prompt {prompt.get('name', 'Unknown')}.")
        elif content_type == "chat" and not isinstance(content, list):
            raise InvalidPromptContentError(f"Prompt content must be a list when type is 'chat' for prompt {prompt.get('name', 'Unknown')}.")
        
        return True


    def _process_prompts(self) -> List[PromptGroup]:
        """
        Process the loaded data and validate against Pydantic models.
        
        Returns:
            List[PromptGroup]: List of validated prompt groups.
        """
        validated_prompts = []
        for wrapper, items in self.data.__dict__.items():
            for item in items:
                try:
                    item_dict = self._convert_to_dict(item)
                    # Wrap content based on 'type'
                    for prompt in item_dict[PROMPTS_ATTR]:
                        self._validate_prompt_structure(prompt)
                        content_type = prompt.get(TYPE_ATTR)
                        if content_type == "chat":
                            prompt[CONTENT_ATTR] = ChatPrompt(content=prompt[CONTENT_ATTR])
                        elif content_type == "text":
                            prompt[CONTENT_ATTR] = TextPrompt(content=prompt[CONTENT_ATTR])
                        else:
                            raise InvalidPromptContentError(f"Unknown content type: {content_type}")
                    prompt_group = PromptGroup(**item_dict)
                    validated_prompts.append(prompt_group)
                except ValidationError as e:
                    # Extract error details and locate specific properties causing the error
                    error_details = []
                    for err in e.errors():
                        error_field = ".".join(str(part) for part in err["loc"])
                        error_message = err["msg"]
                        error_details.append(f"Field '{error_field}' - {error_message}")
                    
                    raise InvalidPromptContentError(
                        f"Invalid prompt content in '{wrapper} ({content_type})': "
                        f"{'; '.join(error_details)}"
                    ) from e

                
                
        return validated_prompts

    def _convert_to_dict(self, obj: Any) -> Any:
        """
        Recursively convert JsonToObject instances to dictionaries.
        
        Args:
            obj (Any): The object to convert.
        
        Returns:
            Any: A dictionary or primitive value.
        """
        if isinstance(obj, JsonToObject):
            return {key: self._convert_to_dict(value) for key, value in obj.__dict__.items()}
        elif isinstance(obj, list):
            return [self._convert_to_dict(item) for item in obj]
        else:
            return obj
    def get_prompt(self, wrapper: str, name: str, version: str) -> Optional[Prompt]:
        """
        Get a specific prompt by wrapper, name and version.
        
        Args:
            wrapper (str): Name of the wrapper.
            name (str): Name of the prompt.
            version (str): Version of the prompt.
            
        Returns:
            Optional[JsonToObject]: The prompt if found, None otherwise.
        """
        for prompt_group in self.prompts:
            if prompt_group.name == wrapper:
                for prompt in prompt_group.prompts:
                    if prompt.name == name and prompt.version == version:
                        return prompt
        return None
    def get_prompt_content(self, wrapper: str, name: str, version: str) -> Optional[Any]:
        """
        Get the content of a specific prompt by wrapper, name and version.
        
        Args:
            wrapper (str): Name of the wrapper.
            name (str): Name of the prompt.
            version (str): Version of the prompt.
            
        Returns:
            Optional[Any]: The content of the prompt if found, None otherwise.
        """
        prompt = self.get_prompt(wrapper, name, version)
        if prompt:
            return prompt.content
        return None

    def get_prompt_output_schema(self, wrapper: str, name: str, version: str) -> Optional[Any]:
        """
        Get the output schema of a specific prompt by wrapper, name and version.
        
        Args:
            wrapper (str): Name of the wrapper.
            name (str): Name of the prompt.
            version (str): Version of the prompt.
                
        Returns:
            Optional[Any]: The output schema of the prompt if found, None otherwise.
        """
        prompt = self.get_prompt(wrapper, name, version)
        if prompt and hasattr(prompt, RESPONSE_FORMAT_ATTR):
            return prompt.response_format
        return None
