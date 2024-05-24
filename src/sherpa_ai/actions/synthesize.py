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

SYNTHESIZE_DESCRIPTION_CITATION = """{role_description}

Context: {context}

Action - Result History:
{history}

Given the context and the action-result history, please complete the task mentioned. If you can cite some of the sentences in the Context, please use them in your response as much intact as possible. DO NOT Include any links you used from the context and history in the result.
Task: {task}
Result:
"""  # noqa: E501


class SynthesizeOutput(BaseAction):
    def __init__(
        self,
        role_description: str,
        llm: BaseLanguageModel,
        description: str = SYNTHESIZE_DESCRIPTION,
        add_citation=False,
        action_usage: str = "Answer the question using conversation history with the user",
    ):
        if add_citation:
            self.description = SYNTHESIZE_DESCRIPTION_CITATION
        else:
            self.description = description
        self.role_description = role_description
        self.llm = llm
        self.action_usage = action_usage

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

    @property
    def usage(self) -> str:
        return self.action_usage
