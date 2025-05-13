"""Validation result model for Sherpa AI output processors.

This module provides the ValidationResult class which represents the outcome
of content validation operations. It includes status, result content, and
optional feedback information.
"""

from pydantic import BaseModel


class ValidationResult(BaseModel):
    """Result of content validation operations.

    This class represents the outcome of validating content, including whether
    the validation passed, the processed content, and any feedback about the
    validation process.

    Attributes:
        is_valid (bool): Whether the validation passed (True) or failed (False).
        result (str): The processed or validated content.
        feedback (str): Additional information about the validation result.

    Example:
        >>> result = ValidationResult(
        ...     is_valid=True,
        ...     result="Validated text",
        ...     feedback="All checks passed"
        ... )
        >>> print(result.is_valid)
        True
        >>> print(result.feedback)
        'All checks passed'
    """

    is_valid: bool
    result: str
    feedback: str = ""

    def __str__(self) -> str:
        """Get string representation of the validation result.

        Returns:
            str: String showing validation status, result, and feedback.

        Example:
            >>> result = ValidationResult(is_valid=True, result="Text", feedback="OK")
            >>> print(str(result))
            'ValidationResult(is_valid=True, result=Text, feedback=OK)'
        """
        return f"ValidationResult(is_valid={self.is_valid}, result={self.result}, feedback={self.feedback})"
