import typing
from typing import Any, List, Optional

from langchain_openai import ChatOpenAI 
from langchain_core.callbacks import ( 
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from langchain_core.language_models import BaseChatModel 
from langchain_core.messages import BaseMessage 
from langchain_core.outputs import ChatResult 
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
