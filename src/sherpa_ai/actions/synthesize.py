from langchain.base_language import BaseLanguageModel

from sherpa_ai.actions.base import BaseAction

SYNTHESIZE_DESCRIPTION = """Role Description: {role_description}
Task: {task}

Context: {context}

Action - Result History:
{history}

Given the context and the action-result history, please provide a solution for the task mentioned.

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
        prompt = self.format(task=task, context=context, history=history)

        result = self.llm.predict(prompt)

        return result
