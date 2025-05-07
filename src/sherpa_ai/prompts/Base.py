"""Base prompt classes for Sherpa AI.

This module provides base classes for defining different types of prompts.
It includes classes for text, chat, and JSON prompts, as well as prompt
groups for organizing related prompts.
"""

from pydantic import BaseModel
from typing import List, Dict, Union


class Prompt(BaseModel):
    """Base class for all prompt types.

    This class defines the common structure for all prompts in the system,
    including metadata and content.

    Attributes:
        name (str): Unique identifier for the prompt.
        description (str): Human-readable description of the prompt's purpose.
        version (str): Version identifier for the prompt.
        content (Union[str, List[Dict[str, str]], Dict]): The actual prompt content.
        variables (Dict): Variables that can be substituted in the prompt.
        response_format (Dict): Expected format of responses to this prompt.

    Example:
        >>> prompt = Prompt(
        ...     name="search_prompt",
        ...     description="Prompt for search queries",
        ...     version="1.0",
        ...     content="Search for {query}",
        ...     variables={"query": ""},
        ...     response_format={"type": "string"}
        ... )
    """
    name: str
    description: str
    version: str
    content: Union[str, List[Dict[str, str]], Dict] 
    variables: Dict
    response_format: Dict


class ChatPrompt(Prompt):
    """Prompt class for chat-based interactions.

    This class represents prompts that consist of a sequence of chat messages,
    typically with alternating roles (e.g., system, user, assistant).

    Attributes:
        content (List[Dict[str, str]]): List of chat messages, each with role
            and content.

    Example:
        >>> chat = ChatPrompt(
        ...     name="greeting",
        ...     description="Chat greeting",
        ...     version="1.0",
        ...     content=[
        ...         {"role": "system", "content": "You are a helpful assistant"},
        ...         {"role": "user", "content": "Hello {name}"}
        ...     ],
        ...     variables={"name": ""},
        ...     response_format={"type": "string"}
        ... )
    """
    content: List[Dict[str, str]]

class TextPrompt(Prompt):
    """Prompt class for simple text-based prompts.

    This class represents prompts that consist of a single text string,
    which may include variable placeholders.

    Attributes:
        content (str): The text content of the prompt.

    Example:
        >>> text = TextPrompt(
        ...     name="query",
        ...     description="Search query prompt",
        ...     version="1.0",
        ...     content="Find information about {topic}",
        ...     variables={"topic": ""},
        ...     response_format={"type": "string"}
        ... )
    """
    content: str

class JsonPrompt(Prompt):
    """Prompt class for JSON-structured prompts.

    This class represents prompts that have a structured JSON format,
    useful for complex templates or structured data.

    Attributes:
        content (Dict): The JSON content of the prompt.

    Example:
        >>> json = JsonPrompt(
        ...     name="api_request",
        ...     description="API request template",
        ...     version="1.0",
        ...     content={"endpoint": "/api/{version}/search"},
        ...     variables={"version": "v1"},
        ...     response_format={"type": "object"}
        ... )
    """
    content: Dict


class PromptGroup(BaseModel):
    """Group of related prompts.

    This class organizes related prompts into a logical group, making it
    easier to manage and retrieve sets of related prompts.

    Attributes:
        name (str): Name of the prompt group.
        description (str): Description of the group's purpose.
        prompts (List[Prompt]): List of prompts in this group.

    Example:
        >>> group = PromptGroup(
        ...     name="search_prompts",
        ...     description="Prompts for search operations",
        ...     prompts=[text_prompt, chat_prompt]
        ... )
    """
    name: str
    description: str
    prompts: List[Prompt]
