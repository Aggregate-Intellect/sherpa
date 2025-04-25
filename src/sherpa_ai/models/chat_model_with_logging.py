"""Chat model with logging functionality for Sherpa AI.

This module provides a wrapper for chat models that adds detailed logging
capabilities. It defines the ChatModelWithLogging class which logs all
model interactions including inputs, outputs, and model information.
"""

import json
import typing
from typing import Any, Coroutine, List, Optional

from langchain_core.callbacks import ( 
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from langchain_core.language_models import BaseChatModel 
from langchain_core.messages import BaseMessage 
from langchain_core.outputs import ChatResult 
from loguru import logger 


class ChatModelWithLogging(BaseChatModel):
    """Chat model wrapper that adds detailed logging functionality.

    This class wraps any chat model to add comprehensive logging of all
    interactions, including input messages, generated responses, and model
    information.

    Attributes:
        llm (BaseChatModel): The underlying chat model to wrap.
        logger (type(logger)): Logger instance for recording interactions.

    Example:
        >>> base_model = ChatOpenAI()
        >>> model = ChatModelWithLogging(llm=base_model, logger=custom_logger)
        >>> response = model.generate([Message("Hello")])
        >>> # Logs will include input, output, and model info
    """

    llm: BaseChatModel
    logger: type(logger) 

    @property
    def _llm_type(self):
        """Get the type of the underlying language model.

        Returns:
            str: Type identifier for the language model.

        Example:
            >>> model = ChatModelWithLogging(llm=ChatOpenAI())
            >>> print(model._llm_type)
            'openai'
        """
        return self.llm._llm_type

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate chat completions with detailed logging.

        This method wraps the underlying model's generation functionality to add
        comprehensive logging of inputs, outputs, and model information.

        Args:
            messages (List[BaseMessage]): List of messages to generate from.
            stop (Optional[List[str]]): List of stop sequences.
            run_manager (Optional[CallbackManagerForLLMRun]): Callback manager.
            **kwargs (Any): Additional arguments for the model.

        Returns:
            ChatResult: Generated chat completion result.

        Example:
            >>> model = ChatModelWithLogging(llm=ChatOpenAI())
            >>> result = model._generate([Message("Hello")])
            >>> print(result.generations[0].text)
            'Hi there!'
            >>> # Check logs for detailed interaction info
        """
        # get the name of the language model. For models like OpenAI, this is the model
        # name (e.g., gpt-3.5-turbo). for other LLMs, this is the type of the LLM
        llm_name = (
            self.llm.model_name if hasattr(self.llm, "model_name") else self._llm_type
        )
        input_text = []
        for message in messages:
            # make sure all the messages stay on the same line
            input_text.append(
                {"text": message.content.replace("\n", "\\n"), "agent": message.type}
            )
        result = self.llm._generate(messages, stop, run_manager, **kwargs)
        # only one generation for a LLM call
        generation = result.generations[0]
        log = {
            "input": input_text,
            # make sure all the messages stay on the same line
            "output": generation.message.content.replace("\n", "\\n"),
            "llm_name": llm_name,
        }
        self.logger.info(json.dumps(log))
        return result

    def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Coroutine[Any, Any, ChatResult]:
        """Asynchronously generate chat completions.

        Args:
            messages (List[BaseMessage]): List of messages in the conversation.
            stop (Optional[List[str]]): List of stop sequences.
            run_manager (Optional[AsyncCallbackManagerForLLMRun]): Callback manager.
            **kwargs (Any): Additional arguments for the model.

        Returns:
            Coroutine[Any, Any, ChatResult]: Coroutine for the generation result.

        Example:
            >>> model = ChatModelWithLogging(llm=ChatOpenAI())
            >>> result = await model._agenerate([Message("Hello")])
            >>> print(result.generations[0].text)
            'Hi there!'
        """
        self.llm.agenerate(messages, stop, run_manager, **kwargs)
