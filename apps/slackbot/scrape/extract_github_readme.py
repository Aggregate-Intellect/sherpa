import requests
import base64
import re
from dotenv import dotenv_values

import pinecone
from langchain.embeddings.openai import OpenAIEmbeddings

from vectorstores import ConversationStore

env_vars = dotenv_values(".env")

# Access the variables
api_key = env_vars.get("API_KEY")
PINECONE_INDEX=env_vars.get("PINECONE_INDEX")
PINECONE_API_KEY=env_vars.get("PINECONE_API_KEY")
PINECONE_ENV=env_vars.get("PINECONE_ENV")
openai_api_key= env_vars.get("OPENAI_KEY")

def get_owner_and_repo(url):
    url_content_list = url.split('/')
    return url_content_list[3], url_content_list[4].split('#')[0]

def extract_github_readme(repo_url):
    pattern = r"(?:https?://)?(?:www\.)?github\.com/.*"
    match = re.match(pattern, repo_url)
    if(match):
        owner, repo = get_owner_and_repo(repo_url)
        path = "README.md"
        token = api_key
        print(token)
        github_api_url = f"https://api.github.com/repos/{owner}/{repo}/contents"
        headers = {"Authorization": f"token {token}", 'X-GitHub-Api-Version': '2022-11-28'}

        response = requests.get(github_api_url, headers=headers)
       
        files = response.json()
        matching_files = [file['name'] for file in files if (
           (file['name'].lower().endswith('.md') or 
            file['name'].lower().endswith('.rst') ) and
            file['name'].lower().startswith('readme')
        )]
        path = matching_files[0]
        github_api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        headers = {"Authorization": f"token {token}", 'X-GitHub-Api-Version': '2022-11-28'}

        response = requests.get(github_api_url, headers=headers)
        data = response.json()
        if "content" in data:
            content = base64.b64decode(data["content"]).decode("utf-8")
            metadata =  [{
                'type': 'github',
                'url': repo_url
            }]
            save_to_pine_cone(content, metadata)
            return content
        else:
            print("README file not found.")


def save_to_pine_cone(content,metadatas):
    pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
    index = pinecone.Index("langchain")
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

    vectorstore = ConversationStore("Github_data", index, embeddings, 'text')
    vectorstore.add_texts(content,metadatas)