import traceback


class SherpaActionExecutionException(Exception):
    """Exception raised when an action fails to execute.
    
    This exception is used to handle errors that occur during the execution of
    actions. It provides a message and a stack trace to help diagnose the issue.
    
    Args:
        message (str): The message to display when the exception is raised.

    Raises:
        SherpaActionExecutionException: If the action fails to execute.
    """
    def __init__(self, message):
        super().__init__(message)
        self.message = message
        self.stacktrace = traceback.format_stack()


class SherpaMissingInformationException(Exception):
    """Exception raised when missing information is required for an action.
    
    This exception is used to handle cases where an action requires additional
    information that is not provided. It provides a message to inform the user
    about the missing information.

    Args:
        message (str): The message to display when the exception is raised.

    Raises:
        SherpaMissingInformationException: If the action fails to execute.
    """
    def __init__(self, message):
        super().__init__(message)
        self.message = message
        self.stacktrace = traceback.format_stack()
