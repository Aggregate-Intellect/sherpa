from langchain.base_language import BaseLanguageModel
from loguru import logger

from sherpa_ai.actions.base import BaseAction

SYNTHESIZE_DESCRIPTION = """{role_description}

Context: {context}

Action - Result History:
{history}

Given the context and the action-result history, please complete the task mentioned. Include any links you used from the context and history in the result.
Task: {task}
Result:
"""  # noqa: E501


class SynthesizeOutput(BaseAction):
    def __init__(
        self,
        role_description: str,
        llm: BaseLanguageModel,
        description: str = SYNTHESIZE_DESCRIPTION,
    ):
        self.role_description = role_description
        self.description = description
        self.llm = llm

    def execute(self, task: str, context: str, history: str) -> str:
        prompt = self.description.format(
            task=task,
            context=context,
            history=history,
            role_description=self.role_description,
        )

        logger.debug("Prompt: {}", prompt)

        result = self.llm.predict(prompt)

        return result

    @property
    def name(self) -> str:
        return "SynthesizeOutput"

    @property
    def args(self) -> dict:
        return {"task": "string", "context": "string", "history": "string"}
