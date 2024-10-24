import json
from typing import Dict, List, Optional, Union

from sherpa_ai.prompts.prompt_loader import PromptLoader

class PromptTemplate(PromptLoader):
    def __init__(self, json_file_path: str):
        super().__init__(json_file_path)
   
    def format_prompt(self, wrapper: str, name: str, version: str, variables: Optional[Dict[str, Union[str, int, float]]] = None) -> Optional[List[Dict[str, str]]]:
        """
        Format a prompt by replacing the placeholders with actual values from variables.

        Args:
            wrapper (str): Name of the wrapper.
            name (str): Name of the prompt.
            version (str): Version of the prompt.
            variables (Optional[Dict[str, Union[str, int, float]]]): The dictionary of variables to replace in the prompt. 
                If None or empty, will use the default from the JSON.

        Returns:
            Optional[List[Dict[str, str]]]: The formatted prompt if found and formatted successfully, None otherwise.
        """
        prompt_content = self.get_prompt_content(wrapper, name, version)
        data = self.get_prompt(wrapper, name, version).variables
        types =  self.get_prompt(wrapper,name, version).type

        variable_from_json = data.__dict__
        final_variables = variable_from_json.copy()

        # Only update the values that are provided in variables
        if variables:
            for key, new_value in variables.items():
                if key in variable_from_json:
                    final_variables[key] = new_value
        
        if not prompt_content:
            return None

        formatted_prompt = []


        if types == "object":

            for message in prompt_content:
                # Access the role and content fields safely
                role = getattr(message, 'role', None)
                content = getattr(message, 'content', None)

                if content:
                        # Replace placeholders in content with the variables
                    for var_name, var_value in final_variables.items():
                        placeholder = f"{{{var_name}}}"
                        if placeholder in content:
                            content = content.replace(placeholder, str(var_value))

                        # Add the formatted content back to the message
                    formatted_message = {
                            "role": role,
                            "content": content
                        }
                    formatted_prompt.append(formatted_message)
                else:
                    formatted_prompt.append({
                            "role": role,
                            "content": ""
                        })
        elif types == "string": 
            content = prompt_content
            for var_name, var_value in final_variables.items():
                placeholder = f"{{{var_name}}}"
                if placeholder in content:
                    content = content.replace(placeholder, str(var_value))
            formatted_prompt.append({
                 content
            })
        return formatted_prompt
    


    def get_full_formatted_prompt(self, wrapper: str, name: str, version: str, 
                                   variables: Optional[Dict[str, Union[str, int, float]]] = None) -> Optional[Dict[str, Union[str, List[Dict]]]]:
        """
        Get the full prompt, including formatted content, description, and output schema.

        Args:
            wrapper (str): Name of the wrapper.
            name (str): Name of the prompt.
            version (str): Version of the prompt.
            variables (Optional[Dict[str, Union[str, int, float]]]): Variables to replace in the prompt.

        Returns:
            Optional[Dict[str, Union[str, List[Dict]]]]: The full formatted prompt with description and schema.
        """
        # Format the prompt
        formatted_content = self.format_prompt(wrapper, name, version, variables)

        if not formatted_content:
            return None

        # Get description
        prompt = self.get_prompt(wrapper, name, version)
        description = getattr(prompt, 'description', '')

        # Get output schema
        output_schema = self.get_prompt_output_schema(wrapper, name, version)

        # Combine all parts into one dictionary
        full_prompt = {
            "description": description,
            "content": formatted_content,
            "output_schema": output_schema
        }

        return full_prompt
