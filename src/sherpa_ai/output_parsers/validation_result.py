from pydantic import BaseModel


class ValidationResult(BaseModel):
    """
    Represents the result of validating a string of content.

    Attributes:
        is_valid (bool): Indicates whether the validation result is valid (True) or not (False).
        result (str): The output of the validation process. A string of validated content.
        feedback (str, optional): Additional feedback or information about the validation result. Default is an empty string.

    Example Usage:
    ```python
    validation_result = ValidationResult(is_valid=True, result="Some validated text", feedback="No issues found.")
    ```

    """

    is_valid: bool
    result: str
    feedback: str = ""
