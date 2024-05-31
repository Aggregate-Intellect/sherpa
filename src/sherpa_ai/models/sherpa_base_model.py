import typing
from typing import Any, List, Optional

from langchain.callbacks.manager import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from langchain.chat_models import ChatOpenAI
from langchain.chat_models.base import BaseChatModel
from langchain.schema import BaseMessage, ChatResult
from pydantic import BaseModel

from sherpa_ai.database.user_usage_tracker import UserUsageTracker


class SherpaOpenAI(ChatOpenAI):
    user_id: typing.Optional[str] = None

    def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ):
        pass

    @property
    def _llm_type(self):
        return super()._llm_type

    def _generate(
        self,
        prompts: List[str],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        response = super()._generate(prompts, stop, run_manager, **kwargs)

        total_token = response.llm_output["token_usage"]["total_tokens"]

        if self.user_id:
            user_db = UserUsageTracker()
            user_db.add_data(user_id=self.user_id, token=total_token)
            user_db.close_connection()

        return response
