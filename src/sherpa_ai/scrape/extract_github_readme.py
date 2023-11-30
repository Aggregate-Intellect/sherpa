import base64
import re

import pinecone
import requests
from dotenv import dotenv_values
from langchain.embeddings.openai import OpenAIEmbeddings
from loguru import logger

import sherpa_ai.config as cfg
from sherpa_ai.connectors.vectorstores import ConversationStore


def get_owner_and_repo(url):
    url_content_list = url.split("/")
    return url_content_list[3], url_content_list[4].split("#")[0]


def extract_github_readme(repo_url):
    pattern = r"(?:https?://)?(?:www\.)?github\.com/.*"
    match = re.match(pattern, repo_url)
    if match:
        owner, repo = get_owner_and_repo(repo_url)
        path = "README.md"
        token = cfg.GITHUB_AUTH_TOKEN
        logger.info(token)
        github_api_url = f"https://api.github.com/repos/{owner}/{repo}/contents"
        headers = {
            "Authorization": f"token {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        response = requests.get(github_api_url, headers=headers)

        files = response.json()
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
        github_api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        headers = {
            "Authorization": f"token {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        response = requests.get(github_api_url, headers=headers)
        data = response.json()
        if "content" in data:
            content = base64.b64decode(data["content"]).decode("utf-8")
            metadata = [{"type": "github", "url": repo_url}]
            try:
                save_to_pine_cone(content, metadata)
            except Exception :
                pass
            return content
        else:
            logger.warning("README file not found.")


def save_to_pine_cone(content, metadatas):
    pinecone.init(api_key=cfg.PINECONE_API_KEY, environment=cfg.PINECONE_ENV)
    index = pinecone.Index("langchain")
    embeddings = OpenAIEmbeddings(openai_api_key=cfg.OPENAI_API_KEY)

    vectorstore = ConversationStore("Github_data", index, embeddings, "text")
    vectorstore.add_texts(content, metadatas)
