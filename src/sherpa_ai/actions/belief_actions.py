"""
Actions to operate the dictionary inside agent's belief
"""

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
        "Update the belief of the agent to store a new key-value pair. The keys can be nested using dot notation."
    )
    belief: Belief

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

    def __str__(self):
        self.usage.format(keys=self.belief.get_all_keys())
        return super().__str__()

    def execute(self, key: str) -> str:
        if not self.belief.has(key):
            return f"Error, key not found in belief, available keys are {self.belief.get_all_keys()}"
        return str(self.belief.get(key))
