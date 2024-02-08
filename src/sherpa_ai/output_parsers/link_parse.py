import re

from loguru import logger

from sherpa_ai.output_parsers.base import BaseOutputParser


class LinkParser(BaseOutputParser):
    """
    A class for parsing and modifying links in text using specified patterns.

    This class inherits from the abstract class BaseOutputParser and provides
    methods to parse and modify links in the input text. It includes functionality
    to replace links with symbols and symbols with links based on predefined patterns.

    Attributes:
    - links (list): A list to store unique links encountered during parsing.
    - link_to_id (dict): A dictionary mapping links to their corresponding symbols.
    - count (int): Counter for generating unique symbols for new links.
    - output_counter (int): Counter for reindexing output.
    - reindex_mapping (dict): A mapping of original document IDs to reindexed IDs.
    - url_pattern (str): Regular expression pattern for identifying links in the input text.
    - doc_id_pattern (str): Regular expression pattern for identifying document IDs in the input text.
    - link_symbol (str): Format string for representing link symbols.

    Methods:
    - parse_output(text: str, tool_output: bool = False) -> str:
        Parses and modifies links in the input text based on the specified patterns.
    """

    def __init__(self):
        """
        Initialize the LinkParser object.
        """
        self.links = []
        self.link_to_id = {}
        self.count = 1

        # for output reindexing
        self.output_counter = 1
        self.reindex_mapping = {}

        self.url_pattern = r"Link:(\S+?)(?:\s|$)"
        self.doc_id_pattern = r"(?:\[)(\d+)(?:\])"

        self.link_symbol = "[{id}]"

    def parse_output(self, text: str, tool_output=False) -> str:
        """
        Parses and modifies links in the input text based on the specified patterns.

        Args:
        - text (str): The input text containing links or symbols to be parsed.
        - tool_output (bool): A flag indicating whether the input text is tool-generated. Default is False.

        Returns:
        - str: The modified text with links replaced by symbols or symbols replaced by links.
        """

        def replace_with_symbol(match: re.Match):
            """
            Replaces links with symbols in the input text.

            Args:
            - match (re.Match): A regular expression match object.

            Returns:
            - str: The modified text with links replaced by symbols.
            """
            link = match.group(1)
            # check if the link is valid
            if not link.startswith("http"):
                link = "http://" + link
            if link not in self.link_to_id:
                self.link_to_id[link] = self.link_symbol.format(id=self.count)
                self.links.append(link)
                self.count += 1

            return "DocID:" + self.link_to_id[link] + "\n"

        def replace_with_link(match: re.Match):
            """
            Replaces symbols with links in the input text.

            Args:
            - match (re.Match): A regular expression match object.

            Returns:
            - str: The modified text with symbols replaced by links.
            """
            logger.debug(match)
            doc_id = int(match.group(1))
            if doc_id <= 0 or doc_id > len(self.links):
                return ""

            if doc_id not in self.reindex_mapping:
                self.reindex_mapping[doc_id] = self.output_counter
                self.output_counter += 1

            result = f"<{self.links[doc_id - 1]}|[{self.reindex_mapping[doc_id]}]>"
            return result

        logger.warning(self.link_to_id)

        if tool_output:
            modified_text = re.sub(self.url_pattern, replace_with_symbol, text)
        else:
            logger.warning(text)
            modified_text = re.sub(self.doc_id_pattern, replace_with_link, text)
            logger.warning(modified_text)
        logger.debug(modified_text)

        return modified_text
