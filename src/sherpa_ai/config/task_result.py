from typing import Literal, Optional

from pydantic import BaseModel


class TaskResult(BaseModel):
    """Represents the result of a task execution.

    This class defines the structure for task execution results, including
    the content of the result and its status.

    Attributes:
        content (str): The content or output of the task execution.
        status (Literal["success", "failed", "waiting"]): The status of the task execution.
            Can be one of "success", "failed", or "waiting". Defaults to "success".

    Example:
        >>> from sherpa_ai.config.task_result import TaskResult
        >>> result = TaskResult(content="Task completed successfully", status="success")
        >>> print(result.content)
        Task completed successfully
        >>> print(result.status)
        success
    """
    content: Optional[str]
    status: Literal["success", "failed", "waiting"] = "success"
