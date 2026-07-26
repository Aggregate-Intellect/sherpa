from __future__ import annotations

import asyncio
import functools
import ipaddress
import json
import re
import socket
from typing import TYPE_CHECKING, Any, List, Optional, Union
from urllib.parse import urljoin, urlparse

import requests
import tiktoken
from loguru import logger

if TYPE_CHECKING:
    from langchain_core.documents import Document
    from langchain_core.language_models import BaseLanguageModel

HTTP_GET_TIMEOUT = 2.5


class UnsafeURLError(ValueError):
    """Raised when a URL fails SSRF safety validation."""


MAX_REDIRECTS = 5


def _is_public_address(ip: str) -> bool:
    """Return True if `ip` is a globally routable, non-internal address.

    Uses ``ipaddress.is_global`` as the primary *allowlist* check: it is the
    logical complement of every special-purpose range IANA has registered
    (loopback, private, link-local, CGNAT 100.64.0.0/10, multicast, reserved,
    unspecified, ...), so it catches ranges an ad-hoc denylist would miss. The
    explicit denylist is kept as belt-and-suspenders defense in depth.
    IPv4-mapped IPv6 addresses (e.g. ``::ffff:127.0.0.1``) are unwrapped first
    so the underlying IPv4 address is evaluated rather than a generic IPv6 one.
    """
    addr = ipaddress.ip_address(ip)
    mapped = getattr(addr, "ipv4_mapped", None)
    if mapped is not None:
        addr = mapped

    if not addr.is_global:
        return False

    return not (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_multicast
        or addr.is_reserved
        or addr.is_unspecified
    )


def assert_safe_url(url: str) -> list[str]:
    """Validate that `url` is http(s) and does not resolve to an internal/
    private/link-local/metadata address, to prevent SSRF via agent- or
    user-controlled URLs (e.g. link scraping tools).

    Args:
        url (str): The URL to validate.

    Returns:
        list[str]: The validated, resolved IP addresses for the host, in
            connection-preference order (IPv4 before IPv6, otherwise as
            returned by the resolver). The caller can pin the connection to
            one of these to avoid a DNS-rebinding TOCTOU window; since not
            every address family is reachable from every network, callers
            should try them in order rather than assume the first always
            connects.

    Raises:
        UnsafeURLError: If the URL's scheme is not http(s), or if its host
            resolves to a non-public address.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise UnsafeURLError(f"URL must conform to HTTP(S) scheme: {url}")

    hostname = parsed.hostname
    if not hostname:
        raise UnsafeURLError(f"URL has no hostname: {url}")

    try:
        # Dedup while preserving the resolver's order (rather than sorting
        # alphabetically, which is a meaningless order that can put an
        # unreachable address family first).
        resolved_ips = list(
            dict.fromkeys(info[4][0] for info in socket.getaddrinfo(hostname, None))
        )
    except socket.gaierror as e:
        raise UnsafeURLError(f"Could not resolve host {hostname}: {e}") from e

    if not resolved_ips or not all(_is_public_address(ip) for ip in resolved_ips):
        raise UnsafeURLError(
            f"URL resolves to a non-public address, refusing to fetch: {url}"
        )

    # Prefer IPv4 first: it's the more universally reachable family, and this
    # is only an ordering preference among already-validated addresses.
    resolved_ips.sort(key=lambda ip: ":" in ip)
    return resolved_ips


def safe_get(
    url: str,
    *,
    headers: Optional[dict] = None,
    timeout: float = HTTP_GET_TIMEOUT,
    max_redirects: int = MAX_REDIRECTS,
    forward_headers_on_redirect: bool = False,
):
    """Perform a GET request hardened against SSRF, redirect and rebinding bypasses.

    Unlike a plain ``requests.get``, this:

    * validates every URL in the redirect chain *before* fetching it, with
      automatic redirect following disabled (``allow_redirects=False``), so an
      attacker-controlled public host cannot 3xx-redirect the request onto an
      internal/metadata address (e.g. ``169.254.169.254``);
    * for plain ``http`` connects directly to the exact IP that just passed
      validation (IP pinning), closing the DNS-rebinding TOCTOU window between
      resolution and connection. For ``https`` the connection is made by
      hostname so TLS SNI / certificate validation still works; the residual
      rebinding window there is the few microseconds between validation and
      connect and is accepted as documented.

    Args:
        url: The URL to fetch.
        headers: Optional headers to send.
        timeout: Per-request timeout in seconds.
        max_redirects: Maximum number of redirect hops to follow.
        forward_headers_on_redirect: If False, the caller-supplied headers
            (which may carry credentials) are only sent on the initial request
            and dropped on redirect hops, to avoid leaking credentials to a
            redirect target.

    Returns:
        requests.Response: The final (non-redirect) response.

    Raises:
        UnsafeURLError: If any URL in the chain fails validation, or if the
            redirect limit is exceeded.
    """
    current_url = url
    base_headers = dict(headers or {})

    for hop in range(max_redirects + 1):
        validated_ips = assert_safe_url(current_url)
        parsed = urlparse(current_url)

        request_headers = dict(base_headers) if (hop == 0 or forward_headers_on_redirect) else {}
        # Host header must be hostname[:port] only — parsed.netloc can carry
        # "user:pass@host" userinfo, which would otherwise leak into the
        # header and produce a malformed Host value.
        host_header = parsed.hostname or ""
        if parsed.port:
            host_header = f"{host_header}:{parsed.port}"

        if parsed.scheme == "http":
            # Pin to a validated IP so the socket connects to exactly an
            # address we vetted, defeating DNS rebinding. Not every address
            # family is reachable from every network, so try each validated
            # IP in preference order rather than assuming the first connects.
            request_headers.setdefault("Host", host_header)
            last_error = None
            for ip in validated_ips:
                host_part = f"[{ip}]" if ":" in ip else ip
                netloc = f"{host_part}:{parsed.port}" if parsed.port else host_part
                connect_url = parsed._replace(netloc=netloc).geturl()
                try:
                    response = requests.get(
                        connect_url,
                        headers=request_headers or None,
                        timeout=timeout,
                        allow_redirects=False,
                    )
                    break
                except requests.exceptions.ConnectionError as e:
                    last_error = e
                    continue
            else:
                raise UnsafeURLError(
                    f"Could not connect to any validated address for {current_url}: {last_error}"
                )
        else:
            response = requests.get(
                current_url,
                headers=request_headers or None,
                timeout=timeout,
                allow_redirects=False,
            )

        if response.status_code in (301, 302, 303, 307, 308):
            location = response.headers.get("Location")
            if not location:
                return response
            current_url = urljoin(current_url, location)
            continue

        return response

    raise UnsafeURLError(f"Too many redirects while fetching: {url}")


def load_files(files: List[str]) -> List[Document]:
    """Load files from a list of file paths.

    Args:
        files (List[str]): A list of file paths to load.

    Returns:
        List[Document]: A list of loaded documents.

    Example:
        >>> from langchain_core.documents import Document
        >>> from sherpa_ai.utils import load_files
        >>> files = ["file1.pdf", "file2.md"]
        >>> documents = load_files(files)
        >>> print(len(documents))
        2
    """
    from langchain_core.documents import Document

    documents = []
    for f in files:
        (f"Loading file {f}")
        if f.endswith(".pdf"):
            text = extract_text_from_pdf(f)
            documents.append(Document(page_content=text, metadata={"source": f}))
        elif f.endswith(".md"):
            with open(f, encoding="utf-8") as md_file:
                text = md_file.read()
            documents.append(Document(page_content=text, metadata={"source": f}))
        elif f.endswith(".gitkeep"):
            pass
        else:
            raise NotImplementedError(f"File type {f} not supported")
    logger.info(documents)
    return documents


def get_links_from_string(text):
    """Extract links from a string.

    Args:
        text (str): The input string to extract links from.

    Returns:
        List[dict]: A list of dictionaries containing the extracted links and their base URLs.

    Example:
        >>> from sherpa_ai.utils import get_links_from_string
        >>> text = "Check out this link: <https://www.example.com>"
        >>> links = get_links_from_string(text)
        >>> print(links)
        [{'url': 'https://www.example.com', 'base_url': 'https://www.example.com'}]
    """
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
    """Get the base URL from a link.

    Args:
        link (str): The input link.

    Returns:
        str: The base URL of the link.

    Example:
        >>> from sherpa_ai.utils import get_base_url
        >>> link = "https://www.example.com/path/to/resource"
        >>> base_url = get_base_url(link)
        >>> print(base_url)
        "https://www.example.com"
    """
    parsed_url = urlparse(link)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return base_url


def scrape_with_url(url: str):
    """Scrape a URL and return the text.

    Args:
        url (str): The URL to scrape.

    Returns:
        dict: A dictionary containing the scraped text and the status code.

    Example:
        >>> from sherpa_ai.utils import scrape_with_url
        >>> url = "https://www.example.com"
        >>> result = scrape_with_url(url)
        >>> print(result)
        {'data': 'Example text', 'status': 200}
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        raise ImportError(
            "Could not import bs4 python package. "
            "This is needed in order to to use scrape_with_url. "
            "Please install it with `pip install beautifulsoup4`."
        )

    response = safe_get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    data = soup.get_text(strip=True)
    status = response.status_code
    if response.status_code == 200:
        return {"data": data, "status": status}
    else:
        return {"data": "", "status": status}


def rewrite_link_references(data: any, question: str):
    """Rewrite link references in a text.

    Args:
        data (any): The input data containing the links.
        question (str): The question to rewrite the links for.

    Returns:
        str: The rewritten text with link references.

    Example:
        >>> from sherpa_ai.utils import rewrite_link_references
        >>> data = [{"link": "https://www.example.com"}]
        >>> question = "What is the link?"
        >>> result = rewrite_link_references(data, question)
        >>> print(result)
        "What is the link? [1] link: https://www.example.com"
    """
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
    """Chunk and summarize text.

    Args:
        text_data (str): The text to chunk and summarize.
        question (str): The question to answer.
        link (str): The link to the text.
        llm (BaseLanguageModel): The language model to use for summarization.

    Returns:
        str: The summarized text.

    Example:
        >>> from sherpa_ai.utils import chunk_and_summarize
        >>> text_data = "This is a test text."
        >>> question = "What is the text?"
        >>> link = "https://www.example.com"
        >>> llm = ChatOpenAI(model="gpt-3.5-turbo")
        >>> result = chunk_and_summarize(text_data, question, link, llm)
        >>> print(result)
        "This is a test text."
    """
    from langchain_text_splitters import TokenTextSplitter

    instruction = (
        "include any information that can be used to answer the "
        f"question '{question}' the given literal text is a data "
        f"from the link {link}. Do not directly answer the question itself"
    )

    text_splitter = TokenTextSplitter(chunk_size=3000, chunk_overlap=0)
    chunked_text = text_splitter.split_text(text_data)
    chunk_summary = []
    for text in chunked_text:
        summarized = llm.invoke(
            f"""Write a concise summary of the following text
            {instruction}:
            "\n\n\n
            f'LITERAL TEXT: {text}
            \n\n\n
            CONCISE SUMMARY: The text is best summarized as"""
        )
        # Chat models return a message object; completion models return a str.
        # Use .text (not .content) since langchain-core 1.x content can be a
        # list of content blocks rather than a plain string.
        summarized = (
            summarized.text if hasattr(summarized, "text") else str(summarized)
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
    """Chunk and summarize a file.

    Args:
        text_data (str): The text to chunk and summarize.
        question (str): The question to answer.
        file_name (str): The name of the file.
        file_format (str): The format of the file.
        llm (BaseLanguageModel): The language model to use for summarization.
        title (str): The title of the file.

    Returns:
        str: The summarized text.

    Example:
        >>> from sherpa_ai.utils import chunk_and_summarize_file
        >>> text_data = "This is a test text."
        >>> question = "What is the text?"
        >>> file_name = "test.txt"
        >>> file_format = "txt"
        >>> llm = ChatOpenAI(model="gpt-3.5-turbo")
        >>> result = chunk_and_summarize_file(text_data, question, file_name, file_format, llm)
        >>> print(result)
        "This is a test text."
    """
    from langchain_text_splitters import TokenTextSplitter

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
        summarized = llm.invoke(
            f"""Write a concise summary of the following text
            {instruction}:
            "\n\n\n
            f'LITERAL TEXT: {text}
            \n\n\n
            CONCISE SUMMARY: The text is best summarized as"""
        )
        # Chat models return a message object; completion models return a str.
        # Use .text (not .content) since langchain-core 1.x content can be a
        # list of content blocks rather than a plain string.
        summarized = (
            summarized.text if hasattr(summarized, "text") else str(summarized)
        )
        chunk_summary.append(summarized)
    return " ".join(chunk_summary)


def question_with_file_reconstructor(
    data: str, file_name: str, title: Union[str, None], file_format: str, question: str
):
    """Reconstruct a question with a file reference.

    Args:
        data (str): The data to reconstruct the question with.
        file_name (str): The name of the file.
        title (str): The title of the file.
        file_format (str): The format of the file.
        question (str): The question to reconstruct.

    Returns:
        str: The reconstructed question.

    Example:
        >>> from sherpa_ai.utils import question_with_file_reconstructor
        >>> data = "This is a test text."
        >>> file_name = "test.txt"
        >>> title = "Test Title"
        >>> file_format = "txt"
        >>> question = "What is the text?"
        >>> result = question_with_file_reconstructor(data, file_name, title, file_format, question)
        >>> print(result)
        "What is the text? [1] link: https://www.example.com"
    """
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
    """Format logs for verbose output.

    Args:
        logs (list): The logs to format.

    Returns:
        str: The formatted logs.
    """
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
    """Modified version of log_formatter that only shows commands.

    Args:
        logs (list): The logs to format.

    Returns:
        str: The formatted logs.
    """
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
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ImportError(
            "Could not import pypdf python package. "
            "This is needed in order to to use extract_text_from_pdf. "
            "Please install it with `pip install pypdf`"
        )
    """Extract text from a PDF file.

    Args:
        pdf_path (str): The path to the PDF file.

    Returns:
        str: The extracted text from the PDF file.
    """
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
    """Extract URLs from a text.

    Args:
        text (str): The text to extract URLs from.

    Returns:
        list: A list of URLs.
    """
    # Split the text into words
    words = text.split()

    # Extract URLs using urllib.parse
    urls = [word for word in words if urlparse(word).scheme in ["http", "https"]]

    return urls


def check_url(url):
    """Check if a URL is valid.

    Args:
        url (str): The URL to check.

    Returns:
        bool: True if the URL is valid, False otherwise.
    """
    if urlparse(url).scheme not in ["http", "https"]:
        raise ValueError(f"URL must conform to HTTP(S) scheme: {url}")

    try:
        _ = safe_get(url)
        return True
    except Exception as e:
        logger.info(f"{e} - {url}")
        return False


def extract_numbers_from_text(text):
    """Extract numbers from a text.

    Args:
        text (str): The text to extract numbers from.

    Returns:
        list: A list of numbers.
    """
    if text is not None:
        text = text.lower()
        text_without_commas = re.sub(",", "", text)
        pattern = r"\d+\.\d+|\d+"
        matches = re.findall(pattern, text_without_commas)
        return matches
    else:
        return []


def word_to_float(text):
    """Convert a word to a float.

    Args:
        text (str): The text to convert to a float.

    Returns:
        dict: A dictionary containing the success and data.
            'success' (bool): True if the conversion was successful, False otherwise.
            'data' (float): The converted float value if 'success' is True.
            'message' (str): An error message if 'success' is False.

    Example:
        >>> from sherpa_ai.utils import word_to_float
        >>> text = "one"
        >>> result = word_to_float(text)
        >>> print(result)
        {'success': True, 'data': 1}
    """
    try:
        from word2number import w2n
    except ImportError:
        raise ImportError(
            "Could not import word2number python package. "
            "This is needed in order to to use word_to_float. "
            "Please install it with `pip install word2number`."
        )

    try:
        result = w2n.word_to_num(text)
        return {"success": True, "data": result}
    except ValueError as e:
        # print(float(ent.text.replace(',' ,'')))
        return {"success": False, "message": e}


# NOTE: A previous NER-based ``extract_numeric_entities`` (spaCy) was removed in
# favor of the lexical ``extract_word_numbers`` below. NER-based extraction was
# context-dependent: the same spelled-out number ("one", "two hundred") could be
# tagged differently depending on the surrounding sentence, so a number present in
# the source could fail to match the same number in a generated answer (and vice
# versa). The lexical matcher is deterministic and context-independent, which is
# what number validation actually needs.


#: Regex matching maximal runs of spelled-out number words, e.g.
#: "one thousand two hundred thirty-four" or "two hundred and five".
_NUMBER_WORD = (
    r"(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|"
    r"thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|"
    r"million|billion|trillion|point)"
)
#: Runs never cross a comma: word-form numbers written with a comma (e.g.
#: "one thousand, two hundred thirty-four") split into separate numbers
#: instead of merging, which is a safer failure mode for validation than
#: treating comma-separated enumerations ("one, two, three") as one phantom
#: number.
_NUMBER_WORD_RUN_PATTERN = re.compile(
    rf"\b{_NUMBER_WORD}(?:(?:[\s-]+(?:and[\s-]+)?){_NUMBER_WORD})*\b",
    re.IGNORECASE,
)

# "one" and "point" are grammatically overloaded in ordinary English ("one" as
# a pronoun/article in "no one", "at one point"; "point" as an ordinary noun),
# so a single bare occurrence of either is not reliably a number and is
# excluded unless it's part of a longer numeric phrase (e.g. "twenty one",
# "two point five"). "point" is additionally rejected at the start/end of a
# match, since it must be flanked by number words on both sides to represent
# a decimal point.
_AMBIGUOUS_STANDALONE = {"one", "point"}


def extract_word_numbers(text: Optional[str]):
    """Extract numbers written as words from a text.

    Finds maximal runs of spelled-out number words (e.g. "one thousand two
    hundred thirty-four") and converts each run to its numeric value. Unlike
    NER-based extraction, this is purely lexical, so the same phrase always
    yields the same number regardless of the surrounding text.

    Args:
        text (Optional[str]): The text to extract word-form numbers from.

    Returns:
        list: A list of numbers as strings (e.g. ["1234", "0.5"]).
    """
    if text is None:
        return []

    numbers = []
    for match in _NUMBER_WORD_RUN_PATTERN.finditer(text.lower()):
        tokens = re.sub(r"[-,]", " ", match.group()).split()

        if len(tokens) == 1 and tokens[0] in _AMBIGUOUS_STANDALONE:
            continue
        if tokens[0] == "point" or tokens[-1] == "point":
            continue
        # A repeated adjacent word (e.g. "one one one") reads as a spoken
        # digit sequence (like a phone number), not an additive/compound
        # number — no legitimate compound number repeats a word back-to-back.
        if any(a == b for a, b in zip(tokens, tokens[1:])):
            continue

        phrase = " ".join(tokens)
        result = word_to_float(phrase)
        if result["success"]:
            numbers.append(str(result["data"]))
    return numbers


def combined_number_extractor(text: str):
    """Extract unique numeric values from a text by combining results from two different extraction methods.

    Combines digit extraction (e.g. "42", "56.45", "123,345") with lexical
    word-number extraction (e.g. "one thousand two hundred thirty-four").
    Both methods are deterministic and context-independent, so the same
    phrase always produces the same set of numbers whether it appears in a
    source document or in a generated answer.

    Args:
        text (str): The text to extract numeric values from.

    Returns:
        list: A list of unique numeric values.
    """
    result = set()
    result.update(extract_numbers_from_text(text))
    result.update(extract_word_numbers(text))

    return list(result)


def verify_numbers_against_source(
    text_to_test: Optional[str], source_text: Optional[str]
):
    """Verify that all numbers in text_to_test exist in source_text.

    Args:
        text_to_test (Optional[str]): The text to test.
        source_text (Optional[str]): The source text.

    Returns:
        tuple: A tuple containing a boolean and a message.
            - boolean: True if all numbers in text_to_test exist in source_text, False otherwise.
            - message: A message indicating whether the numbers in text_to_test exist in source_text.
    """
    candidate_numbers = set(combined_number_extractor(text_to_test))
    source_numbers = set(combined_number_extractor(source_text))

    incorrect_candidates = candidate_numbers - source_numbers

    if len(incorrect_candidates) > 0:
        joined_numbers = ", ".join(incorrect_candidates)
        message = "Don't use the numbers"
        f"{joined_numbers} to answer the question. Instead, stick to the numbers mentioned in the context." 
        return False, message
    return True, None


def check_if_number_exist(result: str, source: str):
    """Check if a number exists in a text.

    Args:
        result (str): The text to check.
        source (str): The source text.

    Returns:
        tuple: A tuple containing a boolean and a message.
            - boolean: True if the number exists in the source text, False otherwise.
            - message: A message indicating whether the number exists in the source text.
    """
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
        message = "Don't use the numbers"
        f"{message} to answer the question instead stick to the numbers mentioned in the context."
        return {"number_exists": False, "messages": message}
    return {"number_exists": True, "messages": message}


def string_comparison_with_jaccard_and_levenshtein(word1, word2, levenshtein_constant):
    """Calculate a combined similarity metric using Jaccard similarity and normalized Levenshtein distance.

    Args:
        word1 (str): First input string.
        word2 (str): Second input string.
        levenshtein_constant (float): Weight for the Levenshtein distance in the combined metric.

    Returns:
    float: Combined similarity metric.
    Args:
    - word1 (str): First input string.
    - word2 (str): Second input string.
    - levenshtein_constant (float): Weight for the Levenshtein distance in the combined metric.

    Returns:
    float: Combined similarity metric.
    """
    from nltk.metrics import edit_distance, jaccard_distance

    word1_set = set(word1)
    word2_set = set(word2)

    lev_distance = edit_distance(word1, word2)
    jaccard_sim = 1 - jaccard_distance(word1_set, word2_set)
    long_len = max(len(word1), len(word2))
    # This will give a value between 0 and 1, where 0 represents identical words
    # and 1 represents completely different words.
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
    NORP (Nationalities or Religious or Political Groups)
    ORG (Organization)
    GPE (Geopolitical Entity)
    LOC (Location) using spaCy.

    Args:
        text (str): The text to extract entities from.

    Returns:
        list: A list of extracted entities.
    """
    try:
        import spacy
    except ImportError:
        raise ImportError(
            "Could not import spacy python package. "
            "This is needed in order to to use extract_entities. "
            "Please install it with `pip install spacy`."
        )

    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    entity_types = ["NORP", "ORG", "GPE", "LOC"]
    filtered_entities = [ent.text for ent in doc.ents if ent.label_ in entity_types]

    return filtered_entities


def json_from_text(text: str):
    """
    Extract and parse JSON data from a text.

    Args:
        text (str): Input text containing JSON data.

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
        source_entity (List[str]): List of entities from the question.
        source (str): Question text.
        result (str): Answer text.
        user_id (str): User ID (optional).
        team_id (str): Team ID (optional).

    Returns:
        dict: Result of the check containing 'entity_exist' and 'messages'.
    """

    instruction = f"""
        I have a question and an answer. I want you to confirm whether the entities from the question are all mentioned in some form within the answer.

        Question = {source}
        Entities inside the question = {source_entity}

        Answer = {result}
       
           only return {{"entity_exist": true , "messages":\"\" }} if all entities are mentioned inside the answer in
           only return {{"entity_exist": false , "messages": \" Entity x hasn't been mentioned inside the answer\"}} if the entity is not mentioned properly .
          """
    llm_result = llm.invoke(instruction)
    checkup_json = json_from_text(llm_result)

    return checkup_json.get("entity_exist", False), checkup_json.get("messages", "")


def text_similarity_by_metrics(check_entity: List[str], source_entity: List[str]):
    """
    Check entity similarity based on Jaccard and Levenshtein metrics.

    Args:
        check_entity (List[str]): List of entities to check.
        source_entity (List[str]): List of reference entities.

    Returns:
        dict: Result of the check containing 'entity_exist' and 'messages'.
    """

    check_entity_lower = [s.lower() for s in check_entity]
    source_entity_lower = [s.lower() for s in source_entity]

    threshold = 0.75
    error_entity = []
    message = ""
    levenshtein_constant = 0.5

    # for each entity in the source entity list, check if it is similar to any entity
    # in the check entity list
    # if similarity is below the threshold, add the entity to the error_entity list
    # else return True means all entities are similar
    for source_entity_val in source_entity_lower:
        metrics_value = 0
        for check_entity_val in check_entity_lower:
            word1 = source_entity_val
            word2 = check_entity_val

            # Calculate the combined similarity metric using Jaccard similarity
            # and normalized Levenshtein distance
            combined_similarity = string_comparison_with_jaccard_and_levenshtein(
                word1=word1, word2=word2, levenshtein_constant=levenshtein_constant
            )

            if metrics_value < combined_similarity:
                metrics_value = combined_similarity
        if metrics_value < threshold:
            # If the metrics value is below the threshold, add the entity to
            # the error_entity list
            index_of_entity = source_entity_lower.index(source_entity_val)
            error_entity.append(source_entity[index_of_entity])

    if len(error_entity) > 0:
        # If there are error entities, create a message to address
        # them in the final answer
        for entity in error_entity:
            message += entity + ", "
        message = f"remember to address these entities {message} in the final answer."
        return False, message
    return True, message


def text_similarity(check_entity: List[str], source_entity: List[str]):
    """
    Check if entities from a reference list are present in another list.

    Args:
        check_entity ([str]): List of entities to check.
        source_entity ([str]): List of reference entities.

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
    """Split a text into chunks of a given size.

    Args:
        data (str): The text to split.
        meta_data (dict): The metadata to include in the chunks.

    Returns:
        dict: A dictionary containing the texts and meta_datas.
    """

    from langchain_text_splitters import CharacterTextSplitter

    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_text(data)
    metadatas = []
    temp_texts = []
    for doc in texts:
        metadatas.append(meta_data)
        temp_texts.append(f"""'file_content': '{doc}' ,{meta_data}""")
    texts = temp_texts

    return {"texts": texts, "meta_datas": metadatas}


def get_links_from_text(text: str) -> List[str]:
    url_regex = r"(https?://\S+|www\.\S+)"
    urls = re.findall(url_regex, text)

    result = [{"url": url, "base_url": get_base_url(url)} for url in urls]
    return result


def is_coroutine_function(func: Any):
    """
    Check if a function is a coroutine function.

    Args:
        func (Any): The function to check.

    Returns:
        bool: True if the function is a coroutine function, False otherwise.
    """
    while isinstance(func, functools.partial):
        func = func.func

    return asyncio.iscoroutinefunction(func) or (
        callable(func) and asyncio.iscoroutinefunction(func.__call__)
    )
