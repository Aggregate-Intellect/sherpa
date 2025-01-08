from typing import Literal

from pydantic import BaseModel


class TaskResult(BaseModel):
    content: str
    status: Literal["success", "failed", "waiting"] = "success"
