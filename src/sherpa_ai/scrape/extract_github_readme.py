import base64
import re

import pinecone 
import requests
from dotenv import dotenv_values 
from langchain_openai import OpenAIEmbeddings 
from loguru import logger 

import sherpa_ai.config as cfg
from sherpa_ai.connectors.vectorstores import ConversationStore


GITHUB_REQUEST_TIMEOUT = 2.5


def get_owner_and_repo(url):
    """
    Extracts the owner and repository name from a GitHub repository URL.

    Parameters:
    - url (str): The GitHub repository URL.

    Returns:
    Tuple[str, str]: A tuple containing the owner and repository name.
    """

    url_content_list = url.split("/")
    return url_content_list[3], url_content_list[4].split("#")[0]


def extract_github_readme(repo_url):
    """
    Extracts the content of the README file from a GitHub repository.

    Parameters:
    - repo_url (str): The GitHub repository URL.

    Returns:
    str or None: The content of the README file, or None if the file is not found.
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
    """
    Saves the content and metadata to Pinecone vector store.

    Parameters:
    - content (str): The content to be saved.
    - metadatas (list): List of metadata associated with the content.
    """

    pinecone.init(api_key=cfg.PINECONE_API_KEY, environment=cfg.PINECONE_ENV)
    index = pinecone.Index("langchain")
    embeddings = OpenAIEmbeddings(openai_api_key=cfg.OPENAI_API_KEY)

    vectorstore = ConversationStore("Github_data", index, embeddings, "text")
    vectorstore.add_texts(content, metadatas)
