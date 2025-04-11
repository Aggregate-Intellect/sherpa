import json
import re
from typing import Callable, Optional, Tuple

from sherpa_ai.actions.base import BaseAction
from sherpa_ai.memory.belief import Belief
from sherpa_ai.policies.exceptions import SherpaPolicyException


def transform_json_output(output_str: str) -> Tuple[str, dict]:
    """
    Transform the output string into an action and arguments

    Args:
        output_str: Output string

    Returns:
        str: Action to be taken
        dict: Arguments for the action

    Raises:
        SherpaPolicyException: If the output does not contain proper json format
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
    """
    Check if the selection of the action is trivial. The selection is trivial if there
    is only one action without any arguments, so LLM is not needed in the selection.

    Args:
        belief (Belief): The current state of the agent

    Returns:
        bool: True if the selection is trivial, False otherwise
    """
    return len(actions) == 1 and len(actions[0].args) == 0


def construct_conversation_from_belief(
    belief: Belief,
    token_counter: Optional[Callable[[str], int]] = None,
    maximum_tokens: int = 4000,
) -> list[tuple[str, str]]:
    """
    Construct a conversation from the belief

    Args:
        belief (Belief): The current state of the agent
        token_counter (Callable[[str], int]): Function to count the tokens in a string
        maximum_tokens (int): Maximum number of tokens in a conversation

    Returns:
        list[tuple[str, str]]: List of conversation turns
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
