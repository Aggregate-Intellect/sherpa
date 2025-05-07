"""Language model integration module for Sherpa AI.

This module provides language model integration for the Sherpa AI system.
It exports the SherpaOpenAI and SherpaChatOpenAI classes which provide
interfaces to OpenAI's language models with Sherpa-specific enhancements.

Example:
    >>> from sherpa_ai.models import SherpaOpenAI, SherpaChatOpenAI
    >>> model = SherpaOpenAI()
    >>> chat_model = SherpaChatOpenAI()
    >>> response = model.generate("Hello")
    >>> chat_response = chat_model.chat("How are you?")
"""

from sherpa_ai.models.sherpa_base_chat_model import SherpaChatOpenAI
from sherpa_ai.models.sherpa_base_model import SherpaOpenAI


__all__ = ["SherpaOpenAI", "SherpaChatOpenAI"]
