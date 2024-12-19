import json
from typing import Dict, List, Optional, Union

from sherpa_ai.prompts.Base import ChatPrompt, TextPrompt
from sherpa_ai.prompts.prompt_loader import PromptLoader


class PromptTemplate(PromptLoader):
    def __init__(self, json_file_path: str):
        super().__init__(json_file_path)

    def format_prompt(
        self,
        wrapper: str,
        name: str,
        version: str,
        variables: Optional[Dict[str, Union[str, int, float]]] = None
    ) -> Optional[Union[str, List[Dict[str, str]]]]:
        """
        Format a prompt by replacing placeholders with actual values from variables.

        Args:
            wrapper (str): Name of the wrapper.
            name (str): Name of the prompt.
            version (str): Version of the prompt.
            variables (Optional[Dict[str, Union[str, int, float]]]): The dictionary of variables to replace in the prompt.
                If None or empty, will use the default from the JSON.

        Returns:
            Optional[Union[str, List[Dict[str, str]]]]: The formatted prompt content if found and successfully formatted.
        """
        prompt = None
        for pg in self.prompts:
            if pg.name == wrapper:
                for p in pg.prompts:
                    if p.name == name and p.version == version:
                        prompt = p
                        break
                break
        
        if not prompt:
            return None

        content = prompt.content
        prompt_variables = prompt.variables or {}
        final_variables = prompt_variables.copy()

        if variables:
            final_variables.update(variables)

        # Check if content is a list (which corresponds to ChatPrompt)
        if isinstance(content, ChatPrompt):
            formatted_prompt = []
            for message in content:
                role = message.get("role")
                text = message.get("content", "")

                # Replace placeholders with variables
                for var_name, var_value in final_variables.items():
                    placeholder = f"{{{var_name}}}"
                    if placeholder in text:
                        text = text.replace(placeholder, str(var_value))

                formatted_prompt.append({"role": role, "content": text})
            return formatted_prompt

        # If content is a TextPrompt, process it like before
        elif isinstance(content, TextPrompt):
            text = content.content
            for var_name, var_value in final_variables.items():
                placeholder = f"{{{var_name}}}"
                if placeholder in text:
                    text = text.replace(placeholder, str(var_value))
            return text

        else:
            raise ValueError(f"Unknown prompt content type: {type(content)}")

    def get_full_formatted_prompt(
        self,
        wrapper: str,
        name: str,
        version: str,
        variables: Optional[Dict[str, Union[str, int, float]]] = None
    ) -> Optional[Dict[str, Union[str, List[Dict[str, str]]]]]:
        """
        Get the full prompt, including formatted content, description, and output schema.

        Args:
            wrapper (str): Name of the wrapper.
            name (str): Name of the prompt.
            version (str): Version of the prompt.
            variables (Optional[Dict[str, Union[str, int, float]]]): Variables to replace in the prompt.

        Returns:
            Optional[Dict[str, Union[str, List[Dict[str, str]]]]]: The full formatted prompt with description and schema.
        """
        prompt = None
        for pg in self.prompts:
            if pg.name == wrapper:
                for p in pg.prompts:
                    if p.name == name and p.version == version:
                        prompt = p
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
