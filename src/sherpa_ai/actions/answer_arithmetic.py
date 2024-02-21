import re

from langchain.base_language import BaseLanguageModel
from loguru import logger

from sherpa_ai.actions.base import BaseAction
from sherpa_ai.actions.math_prompt import MATH_PROMPT
from sherpa_ai.config.task_config import AgentConfig


class AnswerArithmetic(BaseAction):
    def __init__(
        self,
        llm: BaseLanguageModel,
        config: AgentConfig = AgentConfig(),
        placeholder=False,
    ):
        """_summary_

        Args:
            llm (BaseLanguageModel)
            config (AgentConfig, optional): _description_. Defaults to AgentConfig().
            placeholder (bool, optional): If True, use placeholder to replace numeric values in generating Python code.
                Defaults to False.
        """

        self.llm = llm
        self.history = []
        self.placeholder = placeholder

    def replace_numbers_with_placeholders(self, text):
        # Define a regular expression pattern to match both integers and decimals
        number_pattern = re.compile(r"\b\d+(\.\d+)?\b")

        # Use a counter to generate unique placeholders
        placeholder_counter = 1

        # Dictionary to store the mappings between placeholders and numbers
        placeholder_dict = {}

        # Replace each number with a placeholder and store the mapping in the dictionary
        def replace(match):
            nonlocal placeholder_counter
            number = match.group(0)
            placeholder = f"number_{placeholder_counter}"
            placeholder_dict[placeholder] = (
                float(number) if "." in number else int(number)
            )
            placeholder_counter += 1
            return placeholder

        # Use the re.sub function to replace numbers in the text
        result = number_pattern.sub(replace, text)

        return result, placeholder_dict

    def get_code_body(self, code):
        in_solution_function = False
        useful_code = []

        for line in code.splitlines():
            # Check if we are inside the 'solution' function
            if "def solution" in line:
                in_solution_function = True
            elif in_solution_function and "return " in line:
                useful_code.append(line)
                in_solution_function = False

            # Append lines inside the 'solution' function
            if in_solution_function:
                useful_code.append(line)

        return "\n".join(useful_code)

    def execute_code(self, code, arguments):
        namespace = {}
        # Execute the code in the specified namespace
        exec(code, namespace)

        # Call the function with the provided arguments
        result = namespace["solution"](**arguments)
        return result

    def execute(self, question) -> str:
        """
        Answer a math arithmetic question

        Parameters:
            question (str): The mathematical question to be processed.

        Returns:
            str: The answer to the mathematical question.

        Example:
            instance.execute("What is 2 + 2?")
        """
        arguments = {}
        if not self.placeholder:
            prompt = MATH_PROMPT.format(question=question)

        else:
            modified_text, number_dict = self.replace_numbers_with_placeholders(
                question
            )
            scaled_question = modified_text
            prompt = MATH_PROMPT.format(question=scaled_question)
            arguments = number_dict
        code = self.llm.predict(prompt)
        code = self.get_code_body(code)
        result = self.execute_code(code, arguments)

        self.history.append(code)
        logger.info(code)
        return result

    @property
    def name(self) -> str:
        return "Answer Arithmetic question with PAL"

    @property
    def args(self) -> dict:
        return {"question": "string", "replace_holder": "bool"}
