import json
import re
from typing import Tuple

from loguru import logger

from sherpa_ai.actions.base import BaseAction


def transform_json_output(output_str: str) -> Tuple[str, dict]:
    """
    Transform the output string into an action and arguments

    Args:
        output_str: Output string

    Returns:
        str: Action to be taken
        dict: Arguments for the action
    """
    json_pattern = re.compile(r"(\{.*\})", re.DOTALL)
    match = json_pattern.search(output_str)

    if match is not None:
        output = json.loads(match.group(1))
    else:
        logger.error("Output does not contain proper json format {}", output_str)
        return "Finished", None
    command = output["command"]
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
