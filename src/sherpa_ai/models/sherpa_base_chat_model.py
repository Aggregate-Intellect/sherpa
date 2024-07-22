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

from sherpa_ai.database.user_usage_tracker import UserUsageTracker
from sherpa_ai.verbose_loggers.base import BaseVerboseLogger


class SherpaBaseChatModel(BaseChatModel):
    user_id: typing.Optional[str] = None
    verbose_logger: BaseVerboseLogger = None

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
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        response = super()._generate(messages, stop, run_manager, **kwargs)
        token_before = super().get_num_tokens_from_messages(messages)
        token_after = 0
        for result_message in response.generations:
            token_after += super().get_num_tokens(result_message.text)
        total_token = token_before + token_after
        if self.user_id:
            user_db = UserUsageTracker(verbose_logger=self.verbose_logger)
            user_db.add_data(user_id=self.user_id, token=total_token)
            user_db.close_connection()

        return response


class SherpaChatOpenAI(ChatOpenAI):
    user_id: typing.Optional[str] = None
    verbose_logger: BaseVerboseLogger = None

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
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        response = super()._generate(messages, stop, run_manager, **kwargs)
        token_before = super().get_num_tokens_from_messages(messages)
        token_after = 0
        for result_message in response.generations:
            token_after += super().get_num_tokens(result_message.text)
        total_token = token_before + token_after
        if self.user_id:
            user_db = UserUsageTracker(verbose_logger=self.verbose_logger)
            user_db.add_data(user_id=self.user_id, token=total_token)
            user_db.close_connection()

        return response
