import json
import re
from typing import List, Optional, Union
from urllib.parse import urlparse

import requests
import spacy 
import tiktoken 
from bs4 import BeautifulSoup 
from langchain_community.document_loaders import ( 
    UnstructuredMarkdownLoader,
    UnstructuredPDFLoader,
)
from langchain_openai import OpenAI 
from langchain_core.documents import Document 
from langchain_core.language_models import BaseLanguageModel 
from langchain_text_splitters import ( 
    CharacterTextSplitter,
    TokenTextSplitter,
)
from loguru import logger 
from nltk.metrics import edit_distance, jaccard_distance 
from pypdf import PdfReader 
from word2number import w2n 

import sherpa_ai.config as cfg
from sherpa_ai.database.user_usage_tracker import UserUsageTracker
from sherpa_ai.models.sherpa_base_model import SherpaOpenAI


HTTP_GET_TIMEOUT = 2.5


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
    response = requests.get(url, timeout=HTTP_GET_TIMEOUT)
    soup = BeautifulSoup(response.content, "html.parser")
    data = soup.get_text(strip=True)
    status = response.status_code
    if response.status_code == 200:
        return {"data": data, "status": status}
    else:
        return {"data": "", "status": status}


def rewrite_link_references(data: any, question: str):
    result = question + "./n Reference:"
    for count, chunk in enumerate(data):
        reference = f"[{ count + 1}]"
        link = chunk["link"]
        link_with_angle_brackets = f"<{ link }>"
        result = result.replace(link_with_angle_brackets, reference)
        result = result + f""" {reference} link: "{link}" , link_data: {data}"""
        
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


def chunk_and_summarize(text_data: str, question: str, link: str, llm):
    instruction = (
        "include any information that can be used to answer the "
        f"question '{question}' the given literal text is a data "
        f"from the link {link}. Do not directly answer the question itself"
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
    llm,
    title: str = None,
):
    title = f",title {title} " if title is not None else ""

    instruction = (
        f"include any information that can be used to answer the "
        f"question '{question}' the given literal text is a data "
        f"from the file named {file_name}"
        f"{title} and file format {file_format}."
        f"Do not directly answer the question itself"
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


def question_with_file_reconstructor(
    data: str, file_name: str, title: Union[str, None], file_format: str, question: str
):
    result = question + "./n Reference:"
    title = f"'title':'{title}'" if title is not None else ""
    result = (
        result
        + f"""[ {{file_name: '{file_name}' , {title}  , file_format:'{file_format}
            ' , content_of_{file_name}:'{data}'}} ]"""
    )
    return result


# ---- add this for verbose output --- #


def log_formatter(logs):
    """Formats the logger into readable string"""
    log_strings = []
    for log in logs:
        reply = log["reply"]
        if "thoughts" in reply:
            # reply = json.loads(reply)
            formatted_reply = f"""-- Step: {log["Step"]
                                            } -- \nThoughts: \n {reply["thoughts"]} """

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
                formatted_reply = f"""Step: {log["Step"]} \n🛠️{
                    command['name']} \n❓query: {command['args']['query']}"""
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


def extract_urls(text):
    # extract urls from natrual language texts
    # return a list of urls [a,b,c]. Each url is a string

    # Split the text into words
    words = text.split()

    # Extract URLs using urllib.parse
    urls = [word for word in words if urlparse(word).scheme in [
        "http", "https"]]

    return urls


def check_url(url):
    """
    Performs an HTTP GET request on `url` to test its validity.

    Returns True if GET succeeds, False otherwise.
    """

    if urlparse(url).scheme in ["http", "https"]:
        try:
            _ = requests.get(url, timeout=HTTP_GET_TIMEOUT)
            return True
        except Exception as e:
            logger.info(f"{e} - {url}")
            return False
    else:
        raise ValueError(f"URL must conform to HTTP(S) scheme: {url}")


def extract_numbers_from_text(text):
    """Returns a list, possibly empty, of the strings of digits within text"""
    if text is not None:
        text = text.lower()
        text_without_commas = re.sub(",", "", text)
        pattern = r"\d+\.\d+|\d+"
        matches = re.findall(pattern, text_without_commas)
        return matches
    else:
        return []


def word_to_float(text):
    """
    Converts a textual representation of a number to a float.

    Parameters:
    - text (str): The input text containing a textual representation of a number.

    Returns:
    dict: A dictionary with keys:
        - 'success' (bool): True if the conversion was successful, False otherwise.
        - 'data' (float): The converted float value if 'success' is True.
        - 'message' (str): An error message if 'success' is False.
    """

    try:
        result = w2n.word_to_num(text)
        return {"success": True, "data": result}
    except ValueError as e:
        # print(float(ent.text.replace(',' ,'')))
        return {"success": False, "message": e}


def extract_numeric_entities(
    text: Optional[str],
    entity_types: List[str] = ["DATE", "CARDINAL", "QUANTITY", "MONEY"],
):
    """
    Extracts numeric entities from the given text using spaCy and converts textual
    representations of numbers to floats using the word_to_float function.

    Parameters:
    - text (str): The input text from which numeric entities will be extracted.
    - entity_types (List[str]): A list of spaCy entity types to consider for extraction.
                                Default is ["DATE", "CARDINAL", "QUANTITY", "MONEY"].

    Returns:
    List[str]: A list of numeric values extracted from the text.
    """

    if text is None:
        return []

    text = text.lower()
    text = re.sub(r"\s+", " ", text)

    # This loading requires running python -m spacy download en_core_web_sm first
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    numbers = []
    filtered_entities = [
        ent.text for ent in doc.ents if ent.label_ in entity_types]
    for entity in filtered_entities:
        if any(char.isdigit() for char in entity):
            result = extract_numbers_from_text(entity)
            numbers.extend(result)
        else:
            result = word_to_float(entity)
            if result["success"]:
                numbers.append(str(result["data"]))

    return numbers


def combined_number_extractor(text: str):
    """
    Extracts unique numeric values from the given text by combining results
    from two different extraction methods.

    Parameters:
    - text (str): The input text from which numeric values are to be extracted.

    Returns:
    - set: A set containing unique numeric values extracted from the input text.
    """
    result = set()
    result.update(extract_numbers_from_text(text))
    result.update(extract_numeric_entities(text))

    return list(result)


def verify_numbers_against_source(
    text_to_test: Optional[str], source_text: Optional[str]
):
    """Verifies that all numbers in text_to_test exist in source_text. Returns True on success. Returns False and a feedback string on failure."""
    candidate_numbers = set(combined_number_extractor(text_to_test))
    source_numbers = set(combined_number_extractor(source_text))

    incorrect_candidates = candidate_numbers - source_numbers

    if len(incorrect_candidates) > 0:
        joined_numbers = ", ".join(incorrect_candidates)
        message = f"Don't use the numbers"
        f"{joined_numbers} to answer the question. Instead, stick to the numbers mentioned in the context."
        return False, message
    return True, None


def check_if_number_exist(result: str, source: str):
    check_numbers = extract_numbers_from_text(result)
    source_numbers = extract_numbers_from_text(source)
    error_numbers = []
    message = ""
    for data in check_numbers:
        if data not in source_numbers:
            error_numbers.append(data)
    error_numbers = set(error_numbers)
    if len(error_numbers) > 0:
        for numbers in error_numbers:
            message += numbers + ", "
        message = f"Don't use the numbers"
        f"{message} to answer the question instead stick to the numbers mentioned in the context."
        return {"number_exists": False, "messages": message}
    return {"number_exists": True, "messages": message}


def string_comparison_with_jaccard_and_levenshtein(word1, word2, levenshtein_constant):
    """
    Calculate a combined similarity metric using Jaccard similarity and normalized Levenshtein distance.

    Args:
    - word1 (str): First input string.
    - word2 (str): Second input string.
    - levenshtein_constant (float): Weight for the Levenshtein distance in the combined metric.

    Returns:
    float: Combined similarity metric.
    """

    word1_set = set(word1)
    word2_set = set(word2)

    lev_distance = edit_distance(word1, word2)
    jaccard_sim = 1 - jaccard_distance(word1_set, word2_set)
    long_len = max(len(word1), len(word2))
    # This will give a value between 0 and 1, where 0 represents identical words and 1 represents completely different words.
    normalized_levenshtein = 1 - (lev_distance / long_len)
    # The weight is determined by the levenshtein_constant variable,
    # which should be a value between 0 and 1.
    # A higher weight gives more importance to the Levenshtein distance,
    # while a lower weight gives more importance to the Jaccard similarity.
    combined_metric = (levenshtein_constant * normalized_levenshtein) + (
        (1 - levenshtein_constant) * jaccard_sim
    )

    return combined_metric


def extract_entities(text):
    """
    Extract entities of specific types
        NORP (Nationalities or Religious or Political Groups),
        ORG (Organization),
        GPE (Geopolitical Entity),
        LOC (Location) using spaCy.
    Args:
    - text (str): Input text.

    Returns:
    List[str]: List of extracted entities.
    """

    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    entity_types = ["NORP", "ORG", "GPE", "LOC"]
    filtered_entities = [
        ent.text for ent in doc.ents if ent.label_ in entity_types]

    return filtered_entities


def json_from_text(text: str):
    """
    Extract and parse JSON data from a text.

    Args:
    - text (str): Input text containing JSON data.

    Returns:
    dict: Parsed JSON data.
    """
    if isinstance(text, str):
        text = text.replace("\n", "")
        json_pattern = r"\{.*\}"
        json_match = re.search(json_pattern, text)

        if json_match:
            json_data = json_match.group()
            try:
                parsed_json = json.loads(json_data)
                return parsed_json
            except json.JSONDecodeError:
                return {}
        else:
            return {}
    else:
        return {}


def text_similarity_by_llm(
    llm: BaseLanguageModel,
    source_entity: List[str],
    source,
    result,
    user_id=None,
    team_id=None,
):
    """
    Check if entities from a question are mentioned in some form inside the answer using a language model.

    Args:
    - source_entity (List[str]): List of entities from the question.
    - source (str): Question text.
    - result (str): Answer text.
    - user_id (str): User ID (optional).
    - team_id (str): Team ID (optional).

    Returns:
    dict: Result of the check containing 'entity_exist' and 'messages'.
    """

    instruction = f"""
        I have a question and an answer. I want you to confirm whether the entities from the question are all mentioned in some form within the answer.

        Question = {source}
        Entities inside the question = {source_entity}

        Answer = {result}
       """
    prompt = (
        instruction
        + """
           only return {"entity_exist": true , "messages":"" } if all entities are mentioned inside the answer in
           only return {"entity_exist": false , "messages": " Entity x hasn't been mentioned inside the answer"} if the entity is not mentioned properly .
          """
    )

    llm_result = llm.predict(prompt)
    checkup_json = json_from_text(llm_result)

    return checkup_json.get("entity_exist", False), checkup_json.get("messages", "")


def text_similarity_by_metrics(check_entity: List[str], source_entity: List[str]):
    """
    Check entity similarity based on Jaccard and Levenshtein metrics.

    Args:
    - check_entity (List[str]): List of entities to check.
    - source_entity (List[str]): List of reference entities.

    Returns:
    dict: Result of the check containing 'entity_exist' and 'messages'.
    """

    check_entity_lower = [s.lower() for s in check_entity]
    source_entity_lower = [s.lower() for s in source_entity]

    threshold = 0.75
    error_entity = []
    message = ""
    levenshtein_constant = 0.5

    # for each entity in the source entity list, check if it is similar to any entity in the check entity list
    # if similarity is below the threshold, add the entity to the error_entity list
    # else return True means all entities are similar
    for source_entity_val in source_entity_lower:
        metrics_value = 0
        for check_entity_val in check_entity_lower:
            word1 = source_entity_val
            word2 = check_entity_val

            # Calculate the combined similarity metric using Jaccard similarity and normalized Levenshtein distance
            combined_similarity = string_comparison_with_jaccard_and_levenshtein(
                word1=word1, word2=word2, levenshtein_constant=levenshtein_constant
            )

            if metrics_value < combined_similarity:
                metrics_value = combined_similarity
        if metrics_value < threshold:
            # If the metrics value is below the threshold, add the entity to the error_entity list
            index_of_entity = source_entity_lower.index(source_entity_val)
            error_entity.append(source_entity[index_of_entity])

    if len(error_entity) > 0:
        # If there are error entities, create a message to address them in the final answer
        for entity in error_entity:
            message += entity + ", "
        message = f"remember to address these entities {message} in the final answer."
        return False, message
    return True, message


def text_similarity(check_entity: List[str], source_entity: List[str]):
    """
    Check if entities from a reference list are present in another list.

    Args:
    - check_entity ([str]): List of entities to check.
    - source_entity ([str]): List of reference entities.

    Returns:
    dict: Result of the check containing 'entity_exist' and 'messages'.
    """

    error_entity = []
    message = ""
    check_entity_lower = [s.lower() for s in check_entity]
    source_entity_lower = [s.lower() for s in source_entity]
    for entity in source_entity_lower:
        if entity not in check_entity_lower:
            index_of_entity = source_entity_lower.index(entity)
            error_entity.append(source_entity[index_of_entity])
    if len(error_entity) > 0:
        for entity in error_entity:
            message += entity + ", "
        message = f"remember to address these entities {message} in final the answer."
        return False, message
    return True, message


def file_text_splitter(data, meta_data):
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_text(data)
    metadatas = []
    temp_texts = []
    for doc in texts:
        metadatas.append(meta_data)
        temp_texts.append(f"""'file_content': '{doc}' ,{meta_data}""")
    texts = temp_texts

    return {"texts": texts, "meta_datas": metadatas}
