from langchain.base_language import BaseLanguageModel

from sherpa_ai.actions.base import BaseAction

DELIBERATION_DESCRIPTION = """Role Description: {role_description}
Task Description: {task}

Please deliberate on the task and generate a solution that is:

Highly Detailed: Break down components and elements clearly.
Quality-Oriented: Ensure top-notch performance and longevity.
Precision-Focused: Specific measures, materials, or methods to be used.

Keep the result concise and short. No more than one paragraph.

"""  # noqa: E501


class Deliberation(BaseAction):
    # TODO: Make a version of Deliberation action that considers the context
    def __init__(
        self,
        role_description: str,
        llm: BaseLanguageModel,
        description: str = DELIBERATION_DESCRIPTION,
    ):
        self.role_description = role_description
        self.description = description
        self.llm = llm

    @property
    def name(self) -> str:
        return "Deliberation"

    @property
    def args(self) -> dict:
        return {"task": "string"}

    def execute(self, task: str) -> str:
        prompt = self.description.format(
            task=task, role_description=self.role_description
        )

        result = self.llm.predict(prompt)

        return result
