"""
Post-processors for outputs from the LLM.
"""

import re


def md_link_to_slack(text: str) -> str:
    # regex pattern to match Markdown link
    pattern = r"\[([^\]]+)\]\(([^)]+)\)"
    # replace with Slack link
    return re.sub(pattern, r"<\2|\1>", text)
