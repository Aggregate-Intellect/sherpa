"""Output parsing and validation module for Sherpa AI.

This module provides various parsers and validators for processing model outputs.
It includes parsers for links, Markdown to Slack conversion, and validators for
citations, numbers, and entities.

Example:
    >>> from sherpa_ai.output_parsers import LinkParser, NumberValidation
    >>> link_parser = LinkParser()
    >>> links = link_parser.parse("Check out https://example.com")
    >>> number_validator = NumberValidation()
    >>> result = number_validator.validate("The answer is 42")
"""

from sherpa_ai.output_parsers.base import BaseOutputParser, BaseOutputProcessor
from sherpa_ai.output_parsers.citation_validation import CitationValidation
from sherpa_ai.output_parsers.entity_validation import EntityValidation
from sherpa_ai.output_parsers.link_parse import LinkParser
from sherpa_ai.output_parsers.md_to_slack_parse import MDToSlackParse
from sherpa_ai.output_parsers.number_validation import NumberValidation


__all__ = [
    "LinkParser",
    "MDToSlackParse",
    "CitationValidation",
    "NumberValidation",
    "EntityValidation",
]
