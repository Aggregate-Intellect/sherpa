"""Memory management module for Sherpa AI.

This module provides memory management functionality for the Sherpa AI system.
It exports the SharedMemory and Belief classes which handle state management
and belief tracking for agents.

Example:
    >>> from sherpa_ai.memory import SharedMemory, Belief
    >>> memory = SharedMemory()
    >>> belief = Belief()
    >>> memory.store("key", "value")
    >>> belief.update("observation", "action")
"""

from sherpa_ai.memory.belief import Belief
from sherpa_ai.memory.shared_memory import SharedMemory


__all__ = ["SharedMemory", "Belief"]
