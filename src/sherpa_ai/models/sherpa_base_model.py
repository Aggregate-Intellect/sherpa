"""Base OpenAI model integration for Sherpa AI.

This module provides the base OpenAI model integration for the Sherpa AI system.
It defines the SherpaOpenAI class which extends OpenAI's chat model with
Sherpa-specific functionality like usage tracking.
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
from pydantic import BaseModel 

from sherpa_ai.database.user_usage_tracker import UserUsageTracker


class SherpaOpenAI(ChatOpenAI):
    """Enhanced OpenAI chat model with Sherpa-specific features.

    This class extends the OpenAI chat model to add Sherpa-specific functionality,
    particularly user-based token usage tracking. It maintains compatibility with
    the base ChatOpenAI interface while adding user tracking capabilities.

    Attributes:
        user_id (Optional[str]): ID of the user making model requests.

    Example:
        >>> model = SherpaOpenAI(user_id="user123")
        >>> response = model.generate("What is the weather?")
        >>> print(response.generations[0].text)
        'The weather is sunny.'
    """

    user_id: Optional[str] = None

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
            >>> model = SherpaOpenAI()
            >>> print(model._llm_type)
            'openai'
        """
        return super()._llm_type

    def _generate(
        self,
        prompts: List[str],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate chat completions and track token usage.

        This method extends the base generation functionality to track token
        usage per user in the database.

        Args:
            prompts (List[str]): List of prompts to generate from.
            stop (Optional[List[str]]): List of stop sequences.
            run_manager (Optional[CallbackManagerForLLMRun]): Callback manager.
            **kwargs (Any): Additional arguments for the model.

        Returns:
            ChatResult: Generated chat completion result.

        Example:
            >>> model = SherpaOpenAI(user_id="user123")
            >>> result = model._generate(["Hello!"])
            >>> print(result.generations[0].text)
            'Hi there!'
        """
        # Create UsageMetadataCallbackHandler to track token usage
        usage_callback = UsageMetadataCallbackHandler()
        
        # Add the callback to the run manager if provided
        if run_manager:
            run_manager.add_handler(usage_callback)
        
        # Generate response with usage tracking
        response = super()._generate(prompts, stop, run_manager, **kwargs)
        
        # Track usage if user_id is provided
        if self.user_id:
            user_db = UserUsageTracker()
            
            # Extract usage metadata from callback
            usage_metadata = usage_callback.usage_metadata
            
            if usage_metadata:
                # Use the new unified add_usage method
                user_db.add_usage(
                    user_id=self.user_id,
                    usage_metadata=usage_metadata
                )
            else:
                # Fallback to legacy tracking if no usage metadata
                # Extract from response.llm_output as fallback
                total_token = response.llm_output.get("token_usage", {}).get("total_tokens", 0)
                user_db.add_usage(
                    user_id=self.user_id,
                    input_tokens=total_token // 2,  # Rough split for legacy
                    output_tokens=total_token // 2
                )
            
            user_db.close_connection()

        return response
