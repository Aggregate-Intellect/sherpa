import requests
import base64
import re
from dotenv import dotenv_values
from apps.slackbot.vectorstores import ConversationStore
import pinecone
from langchain.embeddings.openai import OpenAIEmbeddings

env_vars = dotenv_values(".env")

# Access the variables
api_key = env_vars.get("API_KEY")
PINECONE_INDEX=env_vars.get("PINECONE_INDEX")
PINECONE_API_KEY=env_vars.get("PINECONE_API_KEY")
PINECONE_ENV=env_vars.get("PINECONE_ENV")
openai_api_key= env_vars.get("OPENAI_KEY")

def get_owner_and_repo(url):
    url_content_list = url.split('/')
    return url_content_list[-2], url_content_list[-1]

def extract_github_readme(url):
    pattern = r"(?:https?://)?(?:www\.)?github\.com/.*"
    match = re.match(pattern, url)
    if(match):
        owner, repo = get_owner_and_repo(url)
        path = "README.md"
        token = api_key
        print(token)
        url = f"https://api.github.com/repos/{owner}/{repo}/contents"
        headers = {"Authorization": f"token {token}", 'X-GitHub-Api-Version': '2022-11-28'}

        response = requests.get(url, headers=headers)
       
        files = response.json()
        matching_files = [file['name'] for file in files if (
           (file['name'].lower().endswith('.md') or 
            file['name'].lower().endswith('.rst') ) and
            file['name'].lower().startswith('readme')
        )]
        path = matching_files[0]
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        headers = {"Authorization": f"token {token}", 'X-GitHub-Api-Version': '2022-11-28'}

        response = requests.get(url, headers=headers)
        data = response.json()
        if "content" in data:
            content = base64.b64decode(data["content"]).decode("utf-8")
            return content
        else:
            print("README file not found.")


def save_to_pine_cone(content):
    pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
    index = pinecone.Index("langchain")
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

    vectorstore = ConversationStore("Github_data", index, embeddings, 'text')
    vectorstore.add_texts(content)


extract_github_readme('https://github.com/TowhidKashem/snapchat-clone')