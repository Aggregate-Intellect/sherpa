import json
from typing import Dict, List, Optional, Union
from sherpa_ai.prompts.Base import ChatPrompt, TextPrompt,JsonPrompt
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
    ) -> Optional[Union[str, List[Dict[str, str]],Dict]]:
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