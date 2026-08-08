"""Language model integration module for Sherpa AI.

This module provides language model integration for the Sherpa AI system.
It exports model wrappers with Sherpa-specific enhancements like usage tracking.

Example:
    >>> from sherpa_ai.models import SherpaLLM
    >>> from langchain_openai import ChatOpenAI
    >>> llm = SherpaLLM(llm=ChatOpenAI(), user_id="user123")
"""

from sherpa_ai.models.sherpa_base_chat_model import SherpaChatOpenAI
from sherpa_ai.models.sherpa_base_model import SherpaOpenAI
from sherpa_ai.models.sherpa_llm import SherpaLLM

__all__ = ["SherpaOpenAI", "SherpaChatOpenAI", "SherpaLLM"]