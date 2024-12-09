from pydantic import BaseModel
from typing import List, Dict, Union


class TextPrompt(BaseModel):
    content: str


class ChatPrompt(BaseModel):
    content: List[Dict[str, str]]


class Prompt(BaseModel):
    name: str
    description: str
    version: str
    content: Union[ChatPrompt, TextPrompt]
    variables: Dict
    response_format: Dict


class PromptGroup(BaseModel):
    name: str
    description: str
    prompts: List[Prompt]
