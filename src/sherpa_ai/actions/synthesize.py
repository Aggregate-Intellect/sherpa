from typing import Any

from langchain_core.language_models import BaseLanguageModel 
from loguru import logger 

from sherpa_ai.actions.base import BaseAction
from sherpa_ai.prompts.prompt_template import PromptTemplate


# SYNTHESIZE_DESCRIPTION = """{role_description}

# Context: {context}

# Action - Result History:
# {history}

# Given the context and the action-result history, please complete the task mentioned. Include any links you used from the context and history in the result.
# Task: {task}
# Result:
# """  # noqa: E501

# SYNTHESIZE_DESCRIPTION_CITATION = """{role_description}

# Context: {context}

# Action - Result History:
# {history}

# Given the context and the action-result history, please complete the task mentioned. If you can cite some of the sentences in the Context, please use them in your response as much intact as possible. DO NOT Include any links you used from the context and history in the result.
# Task: {task}
# Result:
# """  # noqa: E501


class SynthesizeOutput(BaseAction):
    role_description: str
    llm: Any = None  # The BaseLanguageModel from LangChain is not compatible with Pydantic 2 yet
    # description: str = SYNTHESIZE_DESCRIPTION
    add_citation: bool = False

    # Override the name and args from BaseAction
    name: str = "SynthesizeOutput"
    args: dict = {"task": "string", "context": "string", "history": "string"}
    usage: str = "Answer the question using conversation history with the user"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # if self.add_citation:
        #     self.description = SYNTHESIZE_DESCRIPTION_CITATION

    def execute(self, task: str, context: str, history: str) -> str:
       
        # prompt = self.description.format(
        #     task=task,
        #     context=context,
        #     history=history,
        #     role_description=self.role_description,
        # )

        template = PromptTemplate("./sherpa_ai/prompts/prompts.json")
        variables = {
            "role_description": self.role_description,
            "task": task,
            "context": context,
            "history": history,
        }
        prompt = template.format_prompt(
            wrapper="synthesize_prompts",
            name="SYNTHESIZE_DESCRIPTION_CITATION" if self.add_citation else "SYNTHESIZE_DESCRIPTION",
            version="1.0",
            variables=variables
        )
        print('-'*50)
        print(prompt)
        print('-'*50)

        logger.debug("Prompt: {}", prompt)
        result = self.llm.generate(prompt)
        return result

# import json
# from typing import Any

# from langchain_core.language_models import BaseLanguageModel
# from loguru import logger

# from sherpa_ai.actions.base import BaseAction
# from sherpa_ai.prompts.prompt_template import PromptTemplate
 

# class SynthesizeOutput(BaseAction):
#     role_description: str
#     llm: Any = None  # The BaseLanguageModel from LangChain is not compatible with Pydantic 2 yet
#     add_citation: bool = False
#     description: str

#     # Override the name and args from BaseAction
#     name: str = "SynthesizeOutput"
#     args: dict = {"task": "string", "context": "string", "history": "string"}
#     usage: str = "Answer the question using conversation history with the user"

#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)

#         # Load the JSON file and extract description strings
#         with open('./sherpa_ai/prompts/prompts.json', 'r') as f:
#             prompts_data = json.load(f)
#             synthesize_prompts = prompts_data.get("synthesize_prompts", [])
#             for prompt in synthesize_prompts:
#                 if self.add_citation and prompt["name"] == "SYNTHESIZE_DESCRIPTION_CITATION":
#                     self.description = prompt["description"]
#                     break
#                 elif not self.add_citation and prompt["name"] == "SYNTHESIZE_DESCRIPTION":
#                     self.description = prompt["description"]
#                     break

#     def execute(self, task: str, context: str, history: str) -> str:
#         template = PromptTemplate("./sherpa_ai/prompts/prompts.json")
#         variables = {
#             "role_description": self.role_description,
#             "task": task,
#             "context": context,
#             "history": history,
#         }
#         prompt = template.format_prompt(
#             wrapper="synthesize_prompts",
#             name="SYNTHESIZE_DESCRIPTION_CITATION" if self.add_citation else "SYNTHESIZE_DESCRIPTION",
#             version="1.0",
#             # variables=variables
#         )

#         print(prompt, flush=True)
#         logger.debug("Prompt: {}", prompt)
#         result = self.llm.predict(prompt)
#         return result
