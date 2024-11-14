from typing import Dict, List, Optional, Union, Any
import json

# from sherpa_ai.utils import JsonToObject, load_json


SCHEMA_ATTR = "schema"
PROMPTS_ATTR = "prompts"
CONTENT_ATTR = "content"
RESPONSE_FORMAT_ATTR = "response_format"

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
            prompts = item.get('schema', {}).get('prompts', [])
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
        
     # New validation method to ensure prompt structure and types match expected schema
    def _validate_prompt_structure(self, prompt: JsonToObject) -> bool:
        """ 
        Validate that the prompt has the required structure and types.
        
        Args:
            prompt (JsonToObject): The prompt object to validate.

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
            if not hasattr(prompt, attr):
                raise InvalidPromptContentError(f"Prompt must have '{attr}' attribute in the prompt '{prompt.name}'.")
            if not isinstance(getattr(prompt, attr), expected_type):
                raise InvalidPromptContentError(
                    f"Prompt '{attr}' must be of type '{expected_type.__name__}'"
                    f"found '{type(getattr(prompt, attr)).__name__}' instead, in the prompt '{prompt.name}' ."
                )

        # Validate that `content` type matches `type` field specification
        if prompt.type == "string" and not isinstance(prompt.content, str):
            raise InvalidPromptContentError(f"Prompt content must be a string when type is 'string', in the prompt '{prompt.name}'.")
        elif prompt.type == "object" and not isinstance(prompt.content, list):
            raise InvalidPromptContentError(f"Prompt content must be a list when type is 'object', in the prompt '{prompt.name}'.")
        
        return True
        
    def _process_prompts(self) -> Dict:
        """
        Process the raw prompts data into a structured format.
        
        Returns:
            Dict: Processed prompts organized by wrapper
        """
        processed_prompts = {}
        for wrapper_key, wrapper_data in vars(self.data).items():
            if isinstance(wrapper_data, list):
                for prompt_group in wrapper_data:
                    # Raise error if schema is not present
                    if not hasattr(prompt_group, SCHEMA_ATTR):
                        raise InvalidPromptContentError(
                            f"Missing '{SCHEMA_ATTR}' attribute in wrapper '{wrapper_key}'."
                        )
                    
                    # Raise error if prompts are not present in schema
                    if not hasattr(prompt_group.schema, PROMPTS_ATTR):
                        raise InvalidPromptContentError(
                            f"Missing '{PROMPTS_ATTR}' attribute in schema of wrapper '{wrapper_key}'."
                        )
                    
                    wrapper_name = wrapper_key
                    if wrapper_name not in processed_prompts:
                        processed_prompts[wrapper_name] = []
                    
                    # Validate each prompt in the schema before adding
                    for prompt in prompt_group.schema.prompts:
                        # Validation to ensure prompt structure is correct before adding
                        self._validate_prompt_structure(prompt)
                        processed_prompts[wrapper_name].append(prompt)
                        
        return processed_prompts


    def get_prompt(self, wrapper: str, name: str, version: str) -> Optional[JsonToObject]:
        """
        Get a specific prompt by wrapper, name and version.
        
        Args:
            wrapper (str): Name of the wrapper.
            name (str): Name of the prompt.
            version (str): Version of the prompt.
            
        Returns:
            Optional[JsonToObject]: The prompt if found, None otherwise.
        """
        if wrapper in self.prompts:
            for prompt in self.prompts[wrapper]:
                if prompt.name == name and prompt.version == version:
                    self._validate_prompt_structure(prompt)
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
            self._validate_prompt_structure(prompt)
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