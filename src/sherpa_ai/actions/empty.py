from sherpa_ai.actions.base import BaseAction


class EmptyAction(BaseAction):
    """A placeholder action class with no functionality.
    
    This class serves as a base template for creating new actions. It inherits from
    BaseAction but provides no actual implementation, making it useful for:
      - Testing action inheritance
      - Creating new action templates
      - Placeholder actions in development
    
    This class inherits from :class:`BaseAction` and provides:
      - Empty name and arguments
      - No-op execute method
      - Basic usage description
    
    Attributes:
        name (str): Empty string as this is a template class.
        args (dict): Empty dictionary as no arguments are needed.
        usage (str): Basic usage description.
    
    Example:
        >>> from sherpa_ai.actions import EmptyAction
        >>> empty = EmptyAction()
        >>> result = empty.execute()  # Returns None
    """

    # Override the name and args from BaseAction
    name: str = ""
    args: dict = {}
    usage: str = "Make a decision"

    def execute(self, **kwargs) -> str:
        pass
