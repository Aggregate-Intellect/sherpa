"""Link parsing and symbol substitution module for Sherpa AI.

This module provides functionality for parsing and transforming links in text.
It defines the LinkParser class which can convert between links and symbolic
references, maintaining a consistent mapping between them.
"""

import re

from loguru import logger

from sherpa_ai.output_parsers.base import BaseOutputParser


class LinkParser(BaseOutputParser):
    """Parser for converting between links and symbolic references.

    This class handles the conversion of URLs to symbolic references and vice versa,
    maintaining a consistent mapping between them. It can process both raw URLs and
    tool-generated output containing links.

    Attributes:
        links (list): List of unique links encountered during parsing.
        link_to_id (dict): Mapping of links to their symbolic references.
        count (int): Counter for generating unique symbol IDs.
        output_counter (int): Counter for reindexing output symbols.
        reindex_mapping (dict): Mapping of original IDs to reindexed IDs.
        url_pattern (str): Regex pattern for identifying links.
        doc_id_pattern (str): Regex pattern for identifying document IDs.
        link_symbol (str): Format string for link symbols.

    Example:
        >>> parser = LinkParser()
        >>> text = "Check Link:example.com and Link:test.com"
        >>> result = parser.parse_output(text, tool_output=True)
        >>> print(result)
        'DocID:[1]\nDocID:[2]\n'
        >>> back = parser.parse_output("[1] and [2]")
        >>> print(back)
        '<http://example.com|[1]> and <http://test.com|[2]>'
    """

    def __init__(self):
        """Initialize a new LinkParser instance.

        Sets up the initial state for link parsing, including empty collections
        for tracking links and their symbols, and defines regex patterns for
        matching links and document IDs.

        Example:
            >>> parser = LinkParser()
            >>> print(parser.count)
            1
            >>> print(len(parser.links))
            0
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
        """Parse and transform links in text.

        This method either converts URLs to symbolic references (when tool_output
        is True) or converts symbolic references back to clickable links (when
        tool_output is False).

        Args:
            text (str): Text containing either URLs or symbolic references.
            tool_output (bool): Whether the input is from a tool (True) or
                              user-facing text (False).

        Returns:
            str: Text with either URLs converted to symbols or symbols
                converted to clickable links.

        Example:
            >>> parser = LinkParser()
            >>> # Convert URLs to symbols
            >>> result = parser.parse_output("Link:example.com", tool_output=True)
            >>> print(result)
            'DocID:[1]\n'
            >>> # Convert symbols back to links
            >>> result = parser.parse_output("[1]")
            >>> print(result)
            '<http://example.com|[1]>'
        """

        def replace_with_symbol(match: re.Match):
            """Replace matched URLs with symbolic references.

            Args:
                match (re.Match): Regex match object containing the URL.

            Returns:
                str: DocID symbol for the matched URL.

            Example:
                >>> parser = LinkParser()
                >>> match = re.match(r"Link:(\S+)", "Link:example.com")
                >>> result = parser.replace_with_symbol(match)
                >>> print(result)
                'DocID:[1]\n'
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
            """Replace matched symbols with clickable links.

            Args:
                match (re.Match): Regex match object containing the symbol ID.

            Returns:
                str: Clickable link format for the matched symbol.

            Example:
                >>> parser = LinkParser()
                >>> parser.links = ["http://example.com"]
                >>> match = re.match(r"(?:\[)(\d+)(?:\])", "[1]")
                >>> result = parser.replace_with_link(match)
                >>> print(result)
                '<http://example.com|[1]>'
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
