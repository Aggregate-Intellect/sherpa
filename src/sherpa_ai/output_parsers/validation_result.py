from pydantic import BaseModel


class ValidationResult(BaseModel):
    is_valid: bool
    result: str
    feedback: str = ""
