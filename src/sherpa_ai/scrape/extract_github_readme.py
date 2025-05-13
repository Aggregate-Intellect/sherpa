"""GitHub README extraction module for Sherpa AI.

This module provides functionality for extracting and processing README files
from GitHub repositories. It handles authentication, content extraction,
and storage of README content in vector databases.
"""

import base64
import re

import requests
from langchain_openai import OpenAIEmbeddings
from loguru import logger

import sherpa_ai.config as cfg
from sherpa_ai.connectors.vectorstores import ConversationStore

GITHUB_REQUEST_TIMEOUT = 2.5


def get_owner_and_repo(url):
    """Extract owner and repository name from GitHub URL.

    This function parses a GitHub repository URL to extract the owner's
    username and repository name.

    Args:
        url (str): GitHub repository URL (e.g., 'https://github.com/owner/repo').

    Returns:
        tuple[str, str]: A tuple containing:
            - owner (str): Repository owner's username
            - repo (str): Repository name

    Example:
        >>> url = "https://github.com/openai/gpt-3"
        >>> owner, repo = get_owner_and_repo(url)
        >>> print(owner, repo)
        'openai' 'gpt-3'
    """
    url_content_list = url.split("/")
    return url_content_list[3], url_content_list[4].split("#")[0]


def extract_github_readme(repo_url):
    """Extract README content from a GitHub repository.

    This function downloads and extracts the content of a repository's README
    file (either .md or .rst). It also saves the content to a vector store
    for future reference.

    Args:
        repo_url (str): GitHub repository URL.

    Returns:
        Optional[str]: README content if found and successfully extracted,
            None otherwise.

    Example:
        >>> url = "https://github.com/openai/gpt-3"
        >>> content = extract_github_readme(url)
        >>> if content:
        ...     print(content[:50])
        '# GPT-3: Language Models are Few-Shot Learners...'
    """
    pattern = r"(?:https?://)?(?:www\.)?github\.com/.*"
    match = re.match(pattern, repo_url)
    if match:
        owner, repo = get_owner_and_repo(repo_url)
        path = "README.md"
        token = cfg.GITHUB_AUTH_TOKEN
        github_api_url = f"https://api.github.com/repos/"
        f"{owner}/{repo}/contents"
        headers = {
            "Authorization": f"token {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        response = requests.get(
            github_api_url, headers=headers, timeout=GITHUB_REQUEST_TIMEOUT
        )

        files = response.json()
        if type(files) is dict and files["message"].lower() == "bad credentials":
            return None
        matching_files = [
            file["name"]
            for file in files
            if (
                (
                    file["name"].lower().endswith(".md")
                    or file["name"].lower().endswith(".rst")
                )
                and file["name"].lower().startswith("readme")
            )
        ]
        path = matching_files[0]
        github_api_url = f"https://api.github.com/repos/"
        f"{owner}/{repo}/contents/{path}"
        headers = {
            "Authorization": f"token {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        response = requests.get(
            github_api_url, headers=headers, timeout=GITHUB_REQUEST_TIMEOUT
        )
        data = response.json()
        if "content" in data:
            content = base64.b64decode(data["content"]).decode("utf-8")
            metadata = [{"type": "github", "url": repo_url}]
            save_to_pine_cone(content, metadata)
            return content
        else:
            logger.warning("README file not found.")


def save_to_pine_cone(content, metadatas):
    """Save content to Pinecone vector store.

    This function saves text content and associated metadata to a Pinecone
    vector store for efficient retrieval. It uses OpenAI embeddings for
    vectorization.

    Args:
        content (str): Text content to be stored.
        metadatas (list): List of metadata dictionaries for the content.

    Raises:
        ImportError: If pinecone-client package is not installed.

    Example:
        >>> content = "# Project Documentation\\nThis is a guide..."
        >>> metadata = [{"type": "github", "url": "https://github.com/org/repo"}]
        >>> save_to_pine_cone(content, metadata)  # Saves to vector store
    """
    try:
        import pinecone
    except ImportError:
        raise ImportError(
            "Could not import pinecone-client python package. "
            "This is needed in order to to use ConversationStore. "
            "Please install it with `pip install pinecone-client`"
        )

    pinecone.init(api_key=cfg.PINECONE_API_KEY, environment=cfg.PINECONE_ENV)
    index = pinecone.Index("langchain")
    embeddings = OpenAIEmbeddings(openai_api_key=cfg.OPENAI_API_KEY)

    vectorstore = ConversationStore("Github_data", index, embeddings, "text")
    vectorstore.add_texts(content, metadatas)
