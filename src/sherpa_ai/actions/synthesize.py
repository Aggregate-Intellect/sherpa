from typing import Any

from langchain_core.language_models import BaseLanguageModel 
from loguru import logger 

from sherpa_ai.actions.base import BaseAction


class SynthesizeOutput(BaseAction):
    role_description: str
    llm: Any = None  # The BaseLanguageModel from LangChain is not compatible with Pydantic 2 yet
    description: str = None
    add_citation: bool = False

    # Override the name and args from BaseAction
    name: str = "SynthesizeOutput"
    args: dict = {"task": "string", "context": "string", "history": "string"}
    usage: str = "Answer the question using conversation history with the user"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
         

    def execute(self, task: str, context: str, history: str) -> str:
        if self.description:
            prompt =self.description.format(
                task=task,
                context=context,
                history=history,
                role_description=self.role_description,
            )
        else:
            variables = {
                "role_description": self.role_description,
                "task": task,
                "context": context,
                "history": history,
            }
            prompt = self.prompt_template.format_prompt(
                wrapper="synthesize_prompts",
                name="SYNTHESIZE_DESCRIPTION_CITATION" if self.add_citation else "SYNTHESIZE_DESCRIPTION",
                version="1.0",
                variables=variables
            )

        logger.debug("Prompt: {}", prompt)
        prompt_str= str(prompt)
        result = self.llm.predict(prompt_str)
        return result
