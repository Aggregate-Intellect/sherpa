"""
Actions to operate the dictionary inside agent's belief
"""

from loguru import logger

from sherpa_ai.actions.base import BaseAction
from sherpa_ai.memory.belief import Belief


class UpdateBelief(BaseAction):
    class Config:
        arbitrary_types_allowed = True

    name: str = "update_belief"
    args: dict = {
        "key": "str",
        "value": "str",
    }
    usage: str = (
        "Update the belief of the agent to store a new key-value pair. The keys can be nested using dot notation. Existing keys are {keys}."
    )
    belief: Belief

    usage_template: str = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.usage_template = self.usage

    def __str__(self):
        self.usage = self.usage_template.format(keys=self.belief.get_all_keys())
        return super().__str__()

    def execute(self, key: str, value: str) -> str:
        self.belief.set(key, value)

        return "Belief updated successfully"


class RetrieveBelief(BaseAction):
    class Config:
        arbitrary_types_allowed = True

    name: str = "retrieve_belief"
    args: dict = {
        "key": "str",
    }
    usage: str = (
        "Retrieve the value of a key from the agent's belief. The available keys are {keys}"
    )

    belief: Belief

    usage_template: str = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.usage_template = self.usage

    def __str__(self):
        self.usage = self.usage_template.format(keys=self.belief.get_all_keys())

        return super().__str__()

    def execute(self, key: str) -> str:
        if not self.belief.has(key):
            return f"Error, key not found in belief, available keys are {self.belief.get_all_keys()}"
        return str(self.belief.get(key))
