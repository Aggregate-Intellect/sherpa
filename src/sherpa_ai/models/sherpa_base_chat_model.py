"""Chat model integration module for Sherpa AI.

This module provides chat model integration for the Sherpa AI system.
It defines base and OpenAI-specific chat model classes with Sherpa enhancements
like usage tracking and verbose logging.
"""

from typing import Any, List, Optional

from langchain_openai import ChatOpenAI 
from langchain_core.callbacks import ( 
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
    UsageMetadataCallbackHandler,
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

    user_id: Optional[str] = None
    session_id: Optional[str] = None
    agent_name: Optional[str] = None
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
        """Generate chat completions and track token usage using UsageMetadataCallbackHandler.

        This method extends the base generation functionality to track token
        usage per user in the database using LangChain's UsageMetadataCallbackHandler
        for accurate token counting and cost calculation.

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
        # Create UsageMetadataCallbackHandler to track token usage
        usage_callback = UsageMetadataCallbackHandler()
        
        # Add the callback to the run manager if provided
        if run_manager:
            run_manager.add_handler(usage_callback)
        
        # Generate response with usage tracking
        response = super()._generate(messages, stop, run_manager, **kwargs)
        
        # Track usage if user_id is provided
        if self.user_id:
            user_db = UserUsageTracker(verbose_logger=self.verbose_logger)
            
            # Get model name and metadata
            model_name = getattr(self, 'model_name', 'unknown')
            session_id = getattr(self, 'session_id', None)
            agent_name = getattr(self, 'agent_name', None)
            
            # Extract usage metadata from callback
            usage_metadata = usage_callback.usage_metadata
            
            if usage_metadata:
                # Use the new usage metadata-based tracking
                user_db.add_usage(
                    user_id=self.user_id,
                    usage_metadata=usage_metadata,
                    model_name=model_name,
                    session_id=session_id,
                    agent_name=agent_name
                )
            else:
                # Fallback to legacy tracking if no usage metadata
                # This should rarely happen with proper callback integration
                user_db.add_usage(
                    user_id=self.user_id,
                    input_tokens=0,
                    output_tokens=0,
                    model_name=model_name,
                    session_id=session_id,
                    agent_name=agent_name
                )
            
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

    user_id: Optional[str] = None
    session_id: Optional[str] = None
    agent_name: Optional[str] = None
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
        # Create UsageMetadataCallbackHandler to track token usage
        usage_callback = UsageMetadataCallbackHandler()
        
        # Add the callback to the run manager if provided
        if run_manager:
            run_manager.add_handler(usage_callback)
        
        # Generate response with usage tracking
        response = super()._generate(messages, stop, run_manager, **kwargs)
        
        # Track usage if user_id is provided
        if self.user_id:
            user_db = UserUsageTracker(verbose_logger=self.verbose_logger)
            
            # Get model name and metadata
            model_name = getattr(self, 'model_name', 'unknown')
            session_id = getattr(self, 'session_id', None)
            agent_name = getattr(self, 'agent_name', None)
            
            # Extract usage metadata from callback
            usage_metadata = usage_callback.usage_metadata
            
            if usage_metadata:
                # Use the new usage metadata-based tracking
                user_db.add_usage(
                    user_id=self.user_id,
                    usage_metadata=usage_metadata,
                    model_name=model_name,
                    session_id=session_id,
                    agent_name=agent_name
                )
            else:
                # Fallback to legacy tracking if no usage metadata
                # This should rarely happen with proper callback integration
                user_db.add_usage(
                    user_id=self.user_id,
                    input_tokens=0,
                    output_tokens=0,
                    model_name=model_name,
                    session_id=session_id,
                    agent_name=agent_name
                )
            
            user_db.close_connection()

        return response
