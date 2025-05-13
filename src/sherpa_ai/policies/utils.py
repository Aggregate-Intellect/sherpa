"""Policy utility functions for Sherpa AI.

This module provides utility functions for policy implementations.
It includes functions for parsing action outputs, checking action selection
conditions, and constructing conversation histories from belief states.
"""

import json
import re
from typing import Callable, Optional, Tuple

from sherpa_ai.actions.base import BaseAction
from sherpa_ai.memory.belief import Belief
from sherpa_ai.policies.exceptions import SherpaPolicyException


def transform_json_output(output_str: str) -> Tuple[str, dict]:
    """Transform JSON-formatted output string into action and arguments.

    This function extracts action name and arguments from a JSON string
    that follows the format: {"command": {"name": "action", "args": {...}}}
    or {"action": {"name": "action", "args": {...}}}.

    Args:
        output_str (str): JSON-formatted string containing action details.

    Returns:
        Tuple[str, dict]: Action name and arguments dictionary.

    Raises:
        SherpaPolicyException: If output lacks proper JSON format or command.

    Example:
        >>> output = '{"command": {"name": "search", "args": {"query": "python"}}}'
        >>> name, args = transform_json_output(output)
        >>> print(name, args["query"])
        'search' 'python'
    """
    json_pattern = re.compile(r"(\{.*\})", re.DOTALL)
    match = json_pattern.search(output_str)

    if match is not None:
        output = json.loads(match.group(1))
    else:
        raise SherpaPolicyException(
            f"Output does not contain proper json format {output_str}"
        )

    command = output.get("command", output.get("action", None))
    if command is None:
        raise SherpaPolicyException(f"Output does not contain a command {output_str}")
    name = command["name"]
    args = command.get("args", {})
    return name, args


def is_selection_trivial(actions: list[BaseAction]) -> bool:
    """Check if action selection requires no deliberation.

    This function determines if action selection is trivial by checking
    if there is only one action available and it takes no arguments.

    Args:
        actions (list[BaseAction]): List of available actions.

    Returns:
        bool: True if selection is trivial (one action, no args), False otherwise.

    Example:
        >>> actions = [SimpleAction()]  # Action with no arguments
        >>> print(is_selection_trivial(actions))
        True
        >>> actions.append(ComplexAction())  # Multiple actions
        >>> print(is_selection_trivial(actions))
        False
    """
    return len(actions) == 1 and len(actions[0].args) == 0


def construct_conversation_from_belief(
    belief: Belief,
    token_counter: Optional[Callable[[str], int]] = None,
    maximum_tokens: int = 4000,
) -> list[tuple[str, str]]:
    """Construct conversation history from belief state.

    This function extracts action starts and results from the belief state's
    internal events to construct a conversation history, optionally limiting
    the total token count.

    Args:
        belief (Belief): Current belief state containing event history.
        token_counter (Optional[Callable[[str], int]]): Function to count tokens.
        maximum_tokens (int): Maximum total tokens in conversation.

    Returns:
        list[tuple[str, str]]: List of (speaker, message) conversation turns.

    Example:
        >>> belief = Belief()
        >>> belief.update_internal("action_start", "search", content="query")
        >>> belief.update_internal("action_finish", "result", content="found")
        >>> history = construct_conversation_from_belief(belief)
        >>> print(history[0][1])  # First assistant message
        '```json\nquery\n```'
        >>> print(history[1][1])  # First human message
        'Action output: found'
    """
    conversation = []

    for event in belief.internal_events:
        if event.event_type == "action_start":
            action = event.name
            conversation.append(("assistant", f"```json\n{action}\n```"))
        elif event.event_type == "action_finish":
            result = event.outputs
            conversation.append(("human", f"Action output: {result}"))

    if token_counter is None:
        return conversation

    cur_token = 0
    added_conversation = []

    # Add turns from the end of the conversation until the maximum number
    # of tokens is reached
    for turn in reversed(conversation):
        if cur_token + token_counter(turn[1]) > maximum_tokens:
            break
        added_conversation.append(turn)
        cur_token += token_counter(turn[1])

    return list(reversed(added_conversation))
