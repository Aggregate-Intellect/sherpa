"""Generic LLM wrapper with usage tracking for Sherpa AI.

Wraps any LangChain BaseChatModel to add Sherpa's user-level token
usage tracking.  Instead of creating a subclass per provider, pass
any chat model instance and get usage tracking for free.

Usage:
    >>> from langchain_openai import ChatOpenAI
    >>> from sherpa_ai.models.sherpa_llm import SherpaLLM
    >>> llm = SherpaLLM(llm=ChatOpenAI(model="gpt-4o"), user_id="user123")
    >>> result = llm.invoke("Hello")

    >>> from langchain_anthropic import ChatAnthropic
    >>> llm = SherpaLLM(llm=ChatAnthropic(model="claude-sonnet-4-20250514"), user_id="user123")
"""

from typing import Any, List, Optional

from langchain_core.callbacks import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult
from pydantic import ConfigDict

from sherpa_ai.database.user_usage_tracker import UserUsageTracker
from sherpa_ai.models.sherpa_base_chat_model import usage_metadata_from_result
from sherpa_ai.verbose_loggers.base import BaseVerboseLogger


class SherpaLLM(BaseChatModel):
    """Provider-agnostic chat model wrapper with usage tracking.

    Wraps any LangChain ``BaseChatModel`` and intercepts ``_generate``
    to record per-user token usage via ``UserUsageTracker``.  This
    replaces the need for a separate ``Sherpa*`` subclass per provider.

    Attributes:
        llm (BaseChatModel): The underlying LangChain chat model.
        user_id (Optional[str]): User ID for usage tracking.
        session_id (Optional[str]): Session ID for usage tracking.
        agent_name (Optional[str]): Agent name for usage tracking.
        verbose_logger (BaseVerboseLogger): Logger for detailed tracking.

    Example:
        >>> from langchain_openai import ChatOpenAI
        >>> llm = SherpaLLM(llm=ChatOpenAI(), user_id="u1")
        >>> llm.invoke("Hello")
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    llm: BaseChatModel
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    agent_name: Optional[str] = None
    verbose_logger: BaseVerboseLogger = None

    @property
    def _llm_type(self) -> str:
        """Return the type identifier of the wrapped model."""
        return self.llm._llm_type

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate a response and track token usage.

        Delegates to the wrapped model's ``_generate``, then records
        usage metadata if a ``user_id`` is set.

        Args:
            messages: Conversation messages.
            stop: Optional stop sequences.
            run_manager: Optional callback manager.
            **kwargs: Passed through to the wrapped model.

        Returns:
            ChatResult: The wrapped model's response.
        """
        response = self.llm._generate(messages, stop, run_manager, **kwargs)

        if self.user_id:
            self._track_usage(response)

        return response

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Asynchronously generate a response and track token usage.

        Args:
            messages: Conversation messages.
            stop: Optional stop sequences.
            run_manager: Optional async callback manager.
            **kwargs: Passed through to the wrapped model.

        Returns:
            ChatResult: The wrapped model's response.
        """
        response = await self.llm._agenerate(messages, stop, run_manager, **kwargs)

        if self.user_id:
            self._track_usage(response)

        return response

    def _track_usage(self, response: ChatResult) -> None:
        """Record token usage from a chat response.

        Args:
            response: The chat result to extract usage from.
        """
        user_db = UserUsageTracker(verbose_logger=self.verbose_logger)

        model_name = getattr(self.llm, "model_name", None) or getattr(
            self.llm, "model", "unknown"
        )
        usage_metadata = usage_metadata_from_result(response)

        if usage_metadata:
            user_db.add_usage(
                user_id=self.user_id,
                usage_metadata=usage_metadata,
                model_name=model_name,
                session_id=self.session_id,
                agent_name=self.agent_name,
            )
        else:
            user_db.add_usage(
                user_id=self.user_id,
                input_tokens=0,
                output_tokens=0,
                model_name=model_name,
                session_id=self.session_id,
                agent_name=self.agent_name,
            )

        user_db.close_connection()