"""Markdown to Slack format conversion module for Sherpa AI.

This module provides functionality for converting Markdown-formatted text to
Slack-compatible format. It defines the MDToSlackParse class which handles
the conversion of Markdown links to Slack's link format.
"""

import re

from sherpa_ai.output_parsers import BaseOutputParser


class MDToSlackParse(BaseOutputParser):
    """Parser for converting Markdown links to Slack format.

    This class converts Markdown-style links ([text](url)) to Slack's link
    format (<url|text>). It maintains the link text and URL while changing
    only the syntax to match Slack's requirements.

    Attributes:
        pattern (str): Regex pattern for identifying Markdown links.

    Example:
        >>> parser = MDToSlackParse()
        >>> text = "Check out [this link](http://example.com)!"
        >>> result = parser.parse_output(text)
        >>> print(result)
        'Check out <http://example.com|this link>!'
    """

    def __init__(self) -> None:
        """Initialize a new MDToSlackParse instance.

        Sets up the regex pattern for matching Markdown-style links in text.
        """

    def __init__(self) -> None:
        """
        Initialize the MDToSlackParse object with pattern.
        """
        self.pattern = r"\[([^\]]+)\]\(([^)]+)\)"

    def parse_output(self, text: str) -> str:
        """Convert Markdown links to Slack format.

        This method finds all Markdown-style links in the input text and
        converts them to Slack's link format while preserving the link
        text and URL.

        Args:
            text (str): Text containing Markdown-style links.

        Returns:
            str: Text with links converted to Slack format.

        Example:
            >>> parser = MDToSlackParse()
            >>> text = "See [docs](https://docs.com) and [code](https://code.com)"
            >>> result = parser.parse_output(text)
            >>> print(result)
            'See <https://docs.com|docs> and <https://code.com|code>'
        """
        return re.sub(self.pattern, r"<\2|\1>", text)
