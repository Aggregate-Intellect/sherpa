"""Sherpa AI Actions Package.

This package provides a collection of action classes that implement various
functionalities for the Sherpa AI system. Each action represents a specific
capability or operation that can be performed by the system.

Available Actions:
    - ArxivSearch: Search and retrieve information from arXiv papers
    - Deliberation: Process and analyze information for decision making
    - EmptyAction: A placeholder action with no functionality
    - GoogleSearch: Search and retrieve information from Google
    - MockAction: A mock implementation for testing purposes
    - TaskPlanning: Generate and manage task execution plans
    - SynthesizeOutput: Generate synthesized responses from multiple inputs

Example:
    >>> from sherpa_ai.actions import ArxivSearch, TaskPlanning
    >>> arxiv = ArxivSearch(role_description="Research assistant")
    >>> planner = TaskPlanning(role_description="Task planner")
    >>> # Use the actions as needed
"""

from sherpa_ai.actions.arxiv_search import ArxivSearch
from sherpa_ai.actions.deliberation import Deliberation
from sherpa_ai.actions.empty import EmptyAction
from sherpa_ai.actions.google_search import GoogleSearch
from sherpa_ai.actions.mock import MockAction
from sherpa_ai.actions.planning import TaskPlanning
from sherpa_ai.actions.synthesize import SynthesizeOutput

__all__ = [
    "Deliberation",
    "GoogleSearch",
    "TaskPlanning",
    "SynthesizeOutput",
    "ArxivSearch",
    "EmptyAction",
    "MockAction"
]
