"""Chat model integration module for Sherpa AI.

This module provides chat model integration for the Sherpa AI system.
It defines base and OpenAI-specific chat model classes with Sherpa enhancements
like usage tracking and verbose logging.
"""

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
    """Base chat model with Sherpa-specific enhancements.

    This class extends the base chat model to add Sherpa-specific functionality,
    including user-based token usage tracking and verbose logging capabilities.

    Attributes:
        user_id (Optional[str]): ID of the user making model requests.
        verbose_logger (BaseVerboseLogger): Logger for detailed operation tracking.

    Example:
        >>> model = SherpaBaseChatModel(user_id="user123")
        >>> response = model.generate([Message("Hello")])
        >>> print(response.generations[0].text)
        'Hi there!'
    """

    user_id: typing.Optional[str] = None
    verbose_logger: BaseVerboseLogger = None

    def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ):
        """Asynchronously generate chat completions.

        Args:
            messages (List[BaseMessage]): List of messages in the conversation.
            stop (Optional[List[str]]): List of stop sequences.
            run_manager (Optional[AsyncCallbackManagerForLLMRun]): Callback manager.
            **kwargs (Any): Additional arguments for the model.

        Note:
            This is a placeholder method that needs to be implemented.
        """
        pass

    @property
    def _llm_type(self):
        """Get the type of the language model.

        Returns:
            str: Type identifier for the language model.

        Example:
            >>> model = SherpaBaseChatModel()
            >>> print(model._llm_type)
            'base_chat_model'
        """
        return super()._llm_type

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate chat completions and track token usage.

        This method extends the base generation functionality to track token
        usage per user in the database and provide verbose logging.

        Args:
            messages (List[BaseMessage]): List of messages to generate from.
            stop (Optional[List[str]]): List of stop sequences.
            run_manager (Optional[CallbackManagerForLLMRun]): Callback manager.
            **kwargs (Any): Additional arguments for the model.

        Returns:
            ChatResult: Generated chat completion result.

        Example:
            >>> model = SherpaBaseChatModel(user_id="user123")
            >>> result = model._generate([Message("Hello")])
            >>> print(result.generations[0].text)
            'Hi there!'
        """
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
    """Enhanced OpenAI chat model with Sherpa-specific features.

    This class extends the OpenAI chat model to add Sherpa-specific functionality,
    including user-based token usage tracking and verbose logging capabilities.

    Attributes:
        user_id (Optional[str]): ID of the user making model requests.
        verbose_logger (BaseVerboseLogger): Logger for detailed operation tracking.

    Example:
        >>> model = SherpaChatOpenAI(user_id="user123")
        >>> response = model.generate([Message("Hello")])
        >>> print(response.generations[0].text)
        'Hi there!'
    """

    user_id: typing.Optional[str] = None
    verbose_logger: BaseVerboseLogger = None

    def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ):
        """Asynchronously generate chat completions.

        Args:
            messages (List[BaseMessage]): List of messages in the conversation.
            stop (Optional[List[str]]): List of stop sequences.
            run_manager (Optional[AsyncCallbackManagerForLLMRun]): Callback manager.
            **kwargs (Any): Additional arguments for the model.

        Note:
            This is a placeholder method that needs to be implemented.
        """
        pass

    @property
    def _llm_type(self):
        """Get the type of the language model.

        Returns:
            str: Type identifier for the language model.

        Example:
            >>> model = SherpaChatOpenAI()
            >>> print(model._llm_type)
            'openai'
        """
        return super()._llm_type

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate chat completions and track token usage.

        This method extends the OpenAI chat completion functionality to track token
        usage per user in the database and provide verbose logging.

        Args:
            messages (List[BaseMessage]): List of messages to generate from.
            stop (Optional[List[str]]): List of stop sequences.
            run_manager (Optional[CallbackManagerForLLMRun]): Callback manager.
            **kwargs (Any): Additional arguments for the model.

        Returns:
            ChatResult: Generated chat completion result.

        Example:
            >>> model = SherpaChatOpenAI(user_id="user123")
            >>> result = model._generate([Message("Hello")])
            >>> print(result.generations[0].text)
            'Hi there!'
        """
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
