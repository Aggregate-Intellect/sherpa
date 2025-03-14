from typing import Any

from sherpa_ai.actions.base import BaseAction


class EmptyAction(BaseAction):

    # Override the name and args from BaseAction
    name: str = ""
    args: dict = {}
    usage: str = "Make a decision"

    def execute(self) -> str:
        pass
