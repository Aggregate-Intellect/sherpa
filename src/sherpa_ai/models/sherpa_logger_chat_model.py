import json
import typing
from typing import Any, Coroutine, List, Optional

from langchain.callbacks.manager import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
    Callbacks,
)
from langchain.chat_models.base import BaseChatModel
from langchain.schema import BaseMessage, ChatResult
from loguru import logger


class SherpaLoggerLLM(BaseChatModel):
    llm: BaseChatModel
    logger: type(logger)

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
        input_text = []
        for message in messages:
            input_text.append(
                {"text": message.content.replace("\n", "\\n"), "agent": message.type}
            )
        result = self.llm._generate(messages, stop, run_manager, **kwargs)
        generation = result.generations[0]  # only one generation for a LLM call
        log = {
            "input": input_text,
            "output": generation.message.content.replace("\n", "\\n"),
        }
        self.logger.info(json.dumps(log))
        return result

    def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: List[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> Coroutine[Any, Any, ChatResult]:
        self.llm.agenerate(messages, stop, run_manager, **kwargs)
