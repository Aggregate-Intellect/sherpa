"""
Post-processors for outputs from the LLM.
"""

import re

from sherpa_ai.output_parsers import BaseOutputParser


class MDToSlackParse(BaseOutputParser):
    """
    A post-processor for converting Markdown links to Slack-compatible format.

    This class inherits from the BaseOutputParser and provides a method to parse
    and convert Markdown-style links to Slack-compatible format in the input text.

    Attributes:
    - pattern (str): Regular expression pattern for identifying Markdown links.

    Methods:
    - parse_output(text: str) -> str:
        Parses and converts Markdown links to Slack-compatible format in the input text.

    Example Usage:
    ```python
    md_to_slack_parser = MDToSlackParse()
    result = md_to_slack_parser.parse_output("Check out [this link](http://example.com)!")
    ```

    """

    def __init__(self) -> None:
        """
        Initialize the MDToSlackParse object with pattern.
        """
        self.pattern = r"\[([^\]]+)\]\(([^)]+)\)"

    def parse_output(self, text: str) -> str:
        """
        Parses and converts Markdown links to Slack-compatible format in the input text.
        Replace with Slack link

        Args:
        - text (str): The input text containing Markdown-style links.

        Returns:
        - str: The modified text with Markdown links replaced by Slack-compatible links.
        """
        return re.sub(self.pattern, r"<\2|\1>", text)
