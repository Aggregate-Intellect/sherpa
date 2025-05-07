"""
Actions to operate the dictionary inside agent's belief
"""

from loguru import logger

from sherpa_ai.actions.base import BaseAction
from sherpa_ai.memory.belief import Belief
from pydantic import ConfigDict


class UpdateBelief(BaseAction):
    """A class for updating the agent's belief system.
    
    This class provides functionality to store and update key-value pairs in the
    agent's belief system. It supports nested keys using dot notation and maintains
    a template for displaying available keys.
    
    This class inherits from :class:`BaseAction` and provides:
      - Key-value pair storage in the belief system
      - Nested key support using dot notation
      - Dynamic usage template with available keys
    
    Attributes:
        name (str): Name of the action, set to "update_belief".
        args (dict): Arguments required by the action, including "key" and "value".
        usage (str): Description of the action's usage with dynamic key listing.
        belief (Belief): The agent's belief system instance.
        usage_template (str): Template for the usage string.
        model_config (ConfigDict): Configuration for Pydantic model validation.
    
    Example:
        >>> from sherpa_ai.actions import UpdateBelief
        >>> from sherpa_ai.memory.belief import Belief
        >>> belief = Belief()
        >>> updater = UpdateBelief(belief=belief)
        >>> result = updater.execute(key="user.preferences.theme", value="dark")
        >>> print(result)
        Belief updated successfully
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

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
        """Initialize the UpdateBelief action.
        
        Args:
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.usage_template = self.usage

    def __str__(self):
        """String representation of the UpdateBelief action.
        
        Returns:
            str: String representation of the action.
        """
        self.usage = self.usage_template.format(keys=self.belief.get_all_keys())
        return super().__str__()

    def execute(self, key: str, value: str) -> str:
        """Execute the UpdateBelief action.
        
        Args:
            key (str): The key to update.
            value (str): The value to update the key with.

        Returns:
            str: A message indicating that the belief has been updated.

        Raises:
            SherpaActionExecutionException: If the action fails to execute.
        """
        self.belief.set(key, value)

        return "Belief updated successfully"


class RetrieveBelief(BaseAction):
    """A class for retrieving values from the agent's belief system.
    
    This class provides functionality to retrieve values stored in the agent's
    belief system using keys. It supports nested keys using dot notation and
    maintains a template for displaying available keys.
    
    This class inherits from :class:`BaseAction` and provides:
      - Value retrieval from the belief system
      - Nested key support using dot notation
      - Dynamic usage template with available keys
      - Error handling for missing keys
    
    Attributes:
        name (str): Name of the action, set to "retrieve_belief".
        args (dict): Arguments required by the action, including "key".
        usage (str): Description of the action's usage with dynamic key listing.
        belief (Belief): The agent's belief system instance.
        usage_template (str): Template for the usage string.
        model_config (ConfigDict): Configuration for Pydantic model validation.
    
    Example:
        >>> from sherpa_ai.actions import RetrieveBelief
        >>> from sherpa_ai.memory.belief import Belief
        >>> belief = Belief()
        >>> belief.set("user.preferences.theme", "dark")
        >>> retriever = RetrieveBelief(belief=belief)
        >>> result = retriever.execute(key="user.preferences.theme")
        >>> print(result)
        dark
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

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
        """Initialize the RetrieveBelief action.
        
        Args:
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.usage_template = self.usage

    def __str__(self):
        """String representation of the RetrieveBelief action.
        
        Returns:
            str: String representation of the action.
        """
        self.usage = self.usage_template.format(keys=self.belief.get_all_keys())

        return super().__str__()

    def execute(self, key: str) -> str:
        """Execute the RetrieveBelief action.
        
        Args:
            key (str): The key to retrieve.

        Returns:
            str: The value of the key.

        Raises:
            SherpaActionExecutionException: If the action fails to execute.
        """
        if not self.belief.has(key):
            return f"Error, key not found in belief, available keys are {self.belief.get_all_keys()}"
        return str(self.belief.get(key))
