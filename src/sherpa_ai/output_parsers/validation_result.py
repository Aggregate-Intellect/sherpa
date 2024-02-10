from pydantic import BaseModel


class ValidationResult(BaseModel):
    """
    Represents the result of a validation process.

    This class inherits from the Pydantic BaseModel and includes fields
    for indicating the validity of the result, the actual result, and optional feedback.

    Attributes:
    - is_valid (bool): Indicates whether the validation result is valid (True) or not (False).
    - result (str): The actual result of the validation process.
    - feedback (str, optional): Additional feedback or information about the validation result. Default is an empty string.

    Example Usage:
    ```python
    validation_result = ValidationResult(is_valid=True, result="Validated successfully", feedback="No issues found.")
    ```

    """

    is_valid: bool
    result: str
    feedback: str = ""
