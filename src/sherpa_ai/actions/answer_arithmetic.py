from loguru import logger
import os
import re
import types
from collections import Counter
from sherpa_ai.actions.base import BaseAction
from sherpa_ai.config.task_config import AgentConfig
import openai
import pal
from pal.core.interface import timeout
from pal.prompt import math_prompts


def changePlaceholder(question, number_dict):
    for key in number_dict:
        question = question.replace(key, str(number_dict[key]))

    return question


def remove_function_arguments(input_string):
    # Define a regular expression pattern to match the function definition
    left = input_string.index("(")

    new_string = input_string[: left + 1] + "):"
    return new_string


def replace_numbers_with_placeholders(text):
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
        placeholder_dict[placeholder] = float(number) if "." in number else int(number)
        placeholder_counter += 1
        return placeholder

    # Use the re.sub function to replace numbers in the text
    result = number_pattern.sub(replace, text)

    return result, placeholder_dict


def run_with_dict(
    self,
    prompt: str,
    dictionary,
    time_out: float = 10,
    temperature: float = 0.0,
    top_p: float = 1.0,
    max_tokens: int = 1024,
    majority_at: int = None,
):
    code_snippets = self.generate(
        prompt,
        majority_at=majority_at,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
    )

    results = []
    for code in code_snippets:
        with timeout(time_out):
            try:
                code[0] = remove_function_arguments(code[0])
                for i in range(1, len(code)):
                    code[i] = changePlaceholder(code[i], dictionary)
                exec_result = self.execute(code)
            except Exception as e:
                print(e)
                continue
            results.append(exec_result)

    if len(results) == 0:
        print(
            "No results was produced. A common reason is that the generated code snippet is not valid or did not return any results."
        )
        return None

    counter = Counter(results)
    return counter.most_common(1)[0][0]


class AnswerArithmetic(BaseAction):
    def __init__(
        self,
        config: AgentConfig = AgentConfig(),
        MODEL="gpt-3.5-turbo",
        PAL_verbose=True,  # TODO
        placeholder=False,
    ):
        """_summary_

        Args:
            config (AgentConfig, optional): _description_. Defaults to AgentConfig().
            MODEL (str, optional): _description_. Defaults to "gpt-3.5-turbo".
            PAL_verbose (bool, optional): _description_. Defaults to True.
            placeholder (bool, optional): If True, use placeholder to replace numeric values in generating Python code.
                Defaults to False.
        """
        openai.api_key = os.getenv("OPENAI_API_KEY")
        interface = pal.interface.ProgramInterface(
            model=MODEL, get_answer_expr="solution()", verbose=PAL_verbose
        )

        interface.run_with_dict = types.MethodType(run_with_dict, interface)

        self.interface = interface
        self.placeholder = placeholder

    def execute(self, question) -> str:
        """
        Answer a math arithmetic question

        Parameters:
            question (str): The mathematical question to be processed.

        Returns:
            str: The answer to the mathematical question.

        Example:
            instance.execute("What is 2 + 2?", replace_numeric=True)
        """

        if not self.placeholder:
            prompt = math_prompts.MATH_PROMPT.format(question=question)
            answer = self.interface.run(prompt)

        else:
            modified_text, number_dict = replace_numbers_with_placeholders(question)
            scaled_question = modified_text
            prompt = math_prompts.MATH_PROMPT.format(question=scaled_question)
            answer = self.interface.run_with_dict(prompt, number_dict)

        reasoning = self.interface.history[-1][0]
        logger.info(reasoning)
        return answer

    @property
    def name(self) -> str:
        return "Answer Arithmetic question with PAL"

    @property
    def args(self) -> dict:
        return {"question": "string", "replace_holder": "bool"}
