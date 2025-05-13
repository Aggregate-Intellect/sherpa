"""
Post-processors for outputs from the LLM.
"""

import re


def md_link_to_slack(text: str) -> str:
    """Convert Markdown links to Slack links.

    Args:
        text (str): The input text containing Markdown links.

    Returns:
        str: The input text with Markdown links converted to Slack links.

    Example:
        >>> text = "Check out the [website](https://example.com) for more information."
        >>> result = md_link_to_slack(text)
        >>> print(result)
        Check out the <https://example.com|website> for more information.
    """
    # regex pattern to match Markdown link
    pattern = r"\[([^\]]+)\]\(([^)]+)\)"
    # replace with Slack link
    return re.sub(pattern, r"<\2|\1>", text)
