"""Base prompt classes for Sherpa AI.

This module provides base classes for defining different types of prompts.
It includes classes for text, chat, and JSON prompts, as well as prompt
groups for organizing related prompts.
"""

from pydantic import BaseModel
from typing import List, Dict, Union


class PromptVersion(BaseModel):
    """Base class for all prompt versions.

    This class defines the common structure for all prompts in the system,
    including metadata and content.

    Attributes:
        version (str): Version identifier for the prompt.
        change_log (str): Description of changes in this version.
        type (str): The type of prompt (e.g., "text", "chat", "json").
        content (Union[str, List[Dict[str, str]], Dict]): The actual prompt content.
        variables (Dict): Variables that can be substituted in the prompt.
        response_format (Dict): Expected format of responses to this prompt.

        Example:
        >>> prompt = PromptVersion(
        ...     version="1.0",
        ...     change_log="Prompt for search queries",
        ...     type="text",
        ...     content="Search for {query}",
        ...     variables={"query": ""},
        ...     response_format={"type": "string"}
        ... )
    """
    version: str
    change_log: str
    type: str
    content: Union[str, List[Dict[str, str]], Dict]
    variables: Dict
    response_format: Dict


class ChatPromptVersion(PromptVersion):
    """Prompt version class for chat-based interactions.

    This class represents prompts that consist of a sequence of chat messages,
    typically with alternating roles (e.g., system, user, assistant).

    Attributes:
        content (List[Dict[str, str]]): List of chat messages, each with role
            and content.

    Example:
        >>> chat = ChatPromptVersion(
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


class TextPromptVersion(PromptVersion):
    """Prompt version class for simple text-based prompts.

    This class represents a specific version of a prompt that consists of a
    single text string or a list of strings that will be joined.

    Attributes:
        content (Union[str, List[str]]): The text content of the prompt, either as a string
            or as a list of strings that will be joined with spaces.

    Example:
        >>> text = TextPromptVersion(
        ...     name="query",
        ...     description="Search query prompt",
        ...     version="1.0",
        ...     content="Find information about {topic}",
        ...     variables={"topic": ""},
        ...     response_format={"type": "string"}
        ... )
    """
    content: Union[str, List[str]]


class JsonPromptVersion(PromptVersion):
    """Prompt version class for JSON-structured prompts.

    This class represents prompts that have a structured JSON format,
    useful for complex templates or structured data.

    Attributes:
        content (Dict): The JSON content of the prompt.

    Example:
        >>> json = JsonPromptVersion(
        ...     name="api_request",
        ...     description="API request template",
        ...     version="1.0",
        ...     content={"endpoint": "/api/{version}/search"},
        ...     variables={"version": "v1"},
        ...     response_format={"type": "object"}
        ... )
    """
    content: Dict


class Prompt(BaseModel):
    """Base class for all prompt types.

    This class defines the common structure for all prompts in the system,
    including metadata and a list of its versions.

    Attributes:
        prompt_id (str): Unique identifier for the prompt.
        description (str): Human-readable description of the prompt's purpose.
        versions (List[PromptVersion]): A list of different versions of this prompt.
    """
    prompt_id: str
    description: str
    versions: List[PromptVersion]


class PromptGroup(BaseModel):
    """Group of related prompts.

    This class organizes related prompts into a logical group, making it
    easier to manage and retrieve sets of related prompts.

    Attributes:
        prompt_parent_id (str): Name of the prompt group.
        description (str): Description of the group's purpose.
        prompts (List[Prompt]): List of prompts in this group.

    Example:
        >>> group = PromptGroup(
        ...     prompt_parent_id="search_prompts",
        ...     description="Prompts for search operations",
        ...     prompts=[text_prompt, chat_prompt]
        ... )
    """
    prompt_parent_id: str
    description: str
    prompts: List[Prompt]