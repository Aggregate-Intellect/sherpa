from typing import Dict, List, Optional, Union
import json

from sherpa_ai.utils import JsonToObject, load_json
# from sherpa_ai.prompts.json_to_object import JsonToObject

class PromptLoader:
    def __init__(self, json_file_path: str):
        raw_data = load_json(json_file_path)
        # Convert JSON to object
        self.data = JsonToObject()(raw_data)
        self.prompts = self._process_prompts()
    
    def _process_prompts(self) -> Dict:
        """
        Process the raw prompts data into a structured format.
        
        Returns:
            Dict: Processed prompts organized by wrapper
        """
        processed_prompts = {}
        for wrapper_key, wrapper_data in self.data.__dict__.items():
            if isinstance(wrapper_data, list):
                for prompt_group in wrapper_data:
                    if hasattr(prompt_group, 'schema') and hasattr(prompt_group.schema, 'prompts'):
                        wrapper_name = wrapper_key
                        if wrapper_name not in processed_prompts:
                            processed_prompts[wrapper_name] = []
                        processed_prompts[wrapper_name].extend(prompt_group.schema.prompts)
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
                    return prompt
        return None

    def get_prompt_content(self, wrapper: str, name: str, version: str) -> Optional[Union[List[Dict], str]]:
        """
        Get the content of a specific prompt by wrapper, name and version.
        
        Args:
            wrapper (str): Name of the wrapper.
            name (str): Name of the prompt.
            version (str): Version of the prompt.
        
        Returns:
            Optional[Union[List[Dict], str]]: The content of the prompt if found, None otherwise.
        """
        prompt = self.get_prompt(wrapper, name, version)
        if prompt and hasattr(prompt, 'content'):
            return prompt.content
        return None

    def get_prompt_output_schema(self, wrapper: str, name: str, version: str) -> Optional[Union[List[Dict], str]]:
        """
        Get the output schema of a specific prompt by wrapper, name and version.
        
        Args:
            wrapper (str): Name of the wrapper.
            name (str): Name of the prompt.
            version (str): Version of the prompt.
            
        Returns:
            Optional[Union[List[Dict], str]]: The output schema of the prompt if found, None otherwise.
        """
        prompt = self.get_prompt(wrapper, name, version)
        if prompt and hasattr(prompt, 'response_format'):
            return prompt.response_format
        return None

