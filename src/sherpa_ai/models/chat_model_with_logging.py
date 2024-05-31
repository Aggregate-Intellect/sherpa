import json
import typing
from typing import Any, Coroutine, List, Optional

from langchain.callbacks.manager import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from langchain.chat_models.base import BaseChatModel
from langchain.schema import BaseMessage, ChatResult
from loguru import logger


class ChatModelWithLogging(BaseChatModel):
    llm: BaseChatModel
    logger: type(logger)

    @property
    def _llm_type(self):
        return self.llm._llm_type

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
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
        generation = result.generations[0]  # only one generation for a LLM call
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
        self.llm.agenerate(messages, stop, run_manager, **kwargs)
