from pydantic import BaseModel
from typing import List, Dict, Union


class Prompt(BaseModel):
    name: str
    description: str
    version: str
    content: str
    variables: Dict
    response_format: Dict

class ChatPrompt(Prompt):
    content: List[Dict[str, str]]

class TextPrompt(Prompt):
    content: str


class PromptGroup(BaseModel):
    name: str
    description: str
    prompts: List[Prompt]
