from typing import Any

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
    role_description: str
    llm: Any  # The BaseLanguageModel from LangChain is not compatible with Pydantic 2 yet
    description: str = DELIBERATION_DESCRIPTION

    # Override the name and args from BaseAction
    name: str = "Deliberation"
    args: dict = {"task": "string"}
    usage: str = "Directly come up with a solution"

    def execute(self, task: str) -> str:
        prompt = self.description.format(
            task=task, role_description=self.role_description
        )

        result = self.llm.predict(prompt)

        return result
