"""
Post-processors for outputs from the LLM.
"""

import re

from sherpa_ai.output_parsers import BaseOutputParser


class MDToSlackParse(BaseOutputParser):
    def __init__(self) -> None:
        self.pattern = r"\[([^\]]+)\]\(([^)]+)\)"

    def parse_output(self, text: str) -> str:
        # replace with Slack link
        return re.sub(self.pattern, r"<\2|\1>", text)
