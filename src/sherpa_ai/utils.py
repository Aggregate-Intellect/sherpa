import re
from typing import List
from urllib.parse import urlparse

import requests
import tiktoken
from bs4 import BeautifulSoup
from langchain.docstore.document import Document
from langchain.document_loaders import UnstructuredMarkdownLoader, UnstructuredPDFLoader
from langchain.llms import OpenAI
from langchain.text_splitter import TokenTextSplitter
from loguru import logger

import sherpa_ai.config as cfg
from sherpa_ai.models.sherpa_base_model import SherpaOpenAI
from typing import Union

from pypdf import PdfReader


def load_files(files: List[str]) -> List[Document]:
    documents = []
    loader = None
    for f in files:
        (f"Loading file {f}")
        if f.endswith(".pdf"):
            loader = UnstructuredPDFLoader(f)
        elif f.endswith(".md"):
            loader = UnstructuredMarkdownLoader(f)
        elif f.endswith(".gitkeep"):
            pass
        else:
            raise NotImplementedError(f"File type {f} not supported")
        if loader is not None:
            documents.extend(loader.load())
    logger.info(documents)
    return documents


def get_links_from_string(text):
    # Define the regular expression pattern to find links inside angle brackets
    pattern = r"<([^>]*)>"

    # Use re.findall to extract all matches of the pattern in the input string
    matches = re.findall(pattern, text)

    # Filter the matches to keep only the ones that start with "http://" or "https://"
    # links = [match for match in matches if match.startswith(
    #     "http://") or match.startswith("https://")]
    links = []

    for match in matches:
        if match.startswith("http://") or match.startswith("https://"):
            links.append({"url": match, "base_url": get_base_url(match)})
    return links


def get_base_url(link):
    parsed_url = urlparse(link)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return base_url


def get_link_from_slack_client_conversation(data):
    links = []
    for item in data:
        if "blocks" in item:
            for block in item["blocks"]:
                if "elements" in block:
                    for element in block["elements"]:
                        for newElement in element["elements"]:
                            if newElement.get("type") == "link":
                                newUrl = newElement["url"]
                                links.append(
                                    {"url": newUrl,
                                        "base_url": get_base_url(newUrl)}
                                )
    return links


def scrape_with_url(url: str):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    data = soup.get_text(strip=True)
    status = response.status_code
    if response.status_code == 200:
        return {"data": data, "status": status}
    else:
        return {"data": "", "status": status}


def question_reconstructor(data: any, question: str):
    result = question + "./n Reference:"
    count = 1
    for chunk in data:
        chunk_link = f"<{chunk['link']}>"
        result = result.replace(f"{chunk_link}", f"[{count}]")
        result = result + \
            f""" [{count}] link: "{chunk['link']}" , link_data: {data}"""
        count += 1

    return result


def count_string_tokens(string: str, model_name: str) -> int:
    """
    Returns the number of tokens in a text string.

    Args:
        string (str): The text string.
        model_name (str): The name of the encoding to use. (e.g., "gpt-3.5-turbo")

    Returns:
        int: The number of tokens in the text string.
    """
    encoding = tiktoken.encoding_for_model(model_name)
    return len(encoding.encode(string))


def chunk_and_summarize(
    text_data: str,
    question: str,
    link: str,
    team_id: str = None,
    user_id: str = None,
):
    llm = SherpaOpenAI(
        temperature=cfg.TEMPRATURE,
        openai_api_key=cfg.OPENAI_API_KEY,
        user_id=user_id,
        team_id=team_id,
    )

    instruction = (
        "include any information that can be used to answer the "
        "question '{question}' the given literal text is a data "
        "from the link {link}. Do not directly answer the question itself"
    )

    text_splitter = TokenTextSplitter(chunk_size=3000, chunk_overlap=0)
    chunked_text = text_splitter.split_text(text_data)
    chunk_summary = []
    for text in chunked_text:
        summarized = llm.predict(
            f"""Write a concise summary of the following text
            {instruction}:
            "\n\n\n
            f'LITERAL TEXT: {text}
            \n\n\n
            CONCISE SUMMARY: The text is best summarized as"""
        )
        chunk_summary.append(summarized)

    return " ".join(chunk_summary)


def chunk_and_summarize_file(
    text_data: str,
    question: str,
    file_name: str,
    file_format: str,
    title: str = None,
    team_id: str = None,
    user_id: str = None,
):

    llm = SherpaOpenAI(
        temperature=cfg.TEMPRATURE,
        openai_api_key=cfg.OPENAI_API_KEY,
        user_id=user_id,
        team_id=team_id,
    )

    title = f",title {title} " if title is not None else ""

    instruction = (
        "include any information that can be used to answer the "
        "question '{question}' the given literal text is a data "
        "from the file named {file_name} {title} and file format {file_format} . Do not directly answer the question itself"
    )
    text_splitter = TokenTextSplitter(chunk_size=3000, chunk_overlap=0)
    chunked_text = text_splitter.split_text(text_data)
    chunk_summary = []
    for text in chunked_text:
        summarized = llm.predict(
            f"""Write a concise summary of the following text
            {instruction}:
            "\n\n\n
            f'LITERAL TEXT: {text}
            \n\n\n
            CONCISE SUMMARY: The text is best summarized as"""
        )
        chunk_summary.append(summarized)
    return " ".join(chunk_summary)


def question_with_file_reconstructor(data: str, file_name: str, title: Union[str, None], file_format: str,  question: str):
    result = question + "./n Reference:"
    title = f"'title':'{title}'" if title is not None else ""
    result = result + \
        f"""[ {{file_name: '{file_name}' , {title}  , file_format:'{file_format}' , content_of_{file_name}:'{data}'}} ]"""
    return result

# ---- add this for verbose output --- #


def log_formatter(logs):
    """Formats the logger into readable string"""
    log_strings = []
    for log in logs:
        reply = log["reply"]
        if "thoughts" in reply:
            # reply = json.loads(reply)
            formatted_reply = (
                f"""-- Step: {log["Step"]} -- \nThoughts: \n {reply["thoughts"]} """
            )

            if "command" in reply:  # add command if it exists
                formatted_reply += f"""\nCommand: \n {reply["command"]}"""

            log_strings.append(formatted_reply)

        else:  # for final response
            formatted_reply = (
                f"""-- Step: {log["Step"]} -- \nFinal Response: \n {reply}"""
            )
            log_strings.append(formatted_reply)

    log_string = "\n".join(log_strings)
    return log_string


def show_commands_only(logs):
    """Modified version of log_formatter that only shows commands"""
    log_strings = []
    if not isinstance(logs, list):  # for single log, turn it into a list
        logs = [logs]
    for log in logs:
        reply = log["reply"]

        if "command" in reply:
            command = reply["command"]

            if command["name"] != "finish":
                formatted_reply = f"""Step: {log["Step"]} \n🛠️{command['name']} \n❓query: {command['args']['query']}"""
                log_strings.append(formatted_reply)

            else:  # for final response
                formatted_reply = """💡Thought process finished!"""
                log_strings.append(formatted_reply)

    log_string = "\n".join(log_strings)
    return log_string


def extract_text_from_pdf(pdf_path):
    text = ""
    # Extract text from a PDF using PdfReader
    pdf_file = open(pdf_path, "rb")
    pdf_reader = PdfReader(pdf_file)

    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()

    pdf_file.close()
    return text
