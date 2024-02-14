from typing import List
import pal
from pal.prompt import colored_object_prompt, math_prompts
from pal.core.interface import timeout
from collections import Counter
from langchain.base_language import BaseLanguageModel
from loguru import logger
import types
import openai
import os
from sherpa_ai.action_planner import ActionPlanner
from sherpa_ai.actions import Deliberation, GoogleSearch, SynthesizeOutput
from sherpa_ai.actions.base import BaseAction
from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.memory import Belief, SharedMemory
from sherpa_ai.verbose_loggers.verbose_loggers import DummyVerboseLogger
import re

MATH_DESCRIPTION = "You are a Mathematician with a deep-rooted expertise in understanding and analyzing the fundamental principles of math. Your primary role is to assist individuals, organizations, and researchers in navigating and resolving complex math-related challenges, using your knowledge to guide decisions and ensure the accuracy and reliability of outcomes."  # noqa: E501

ACTION_PLAN_DESCRIPTION = "Given your specialized expertise, historical context, and your mission to facilitate physics-based solutions, determine which action and its corresponding arguments would be the most scientifically sound and efficient approach to achieve the described task."  # noqa: E501


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


class Mathematician(BaseAgent):
    """
    The Mathematician agent answers arithmatic questions
    """

    def __init__(
        self,
        llm: BaseLanguageModel,
        name="Mathematician",
        description=MATH_DESCRIPTION,
        shared_memory: SharedMemory = None,
        num_runs=3,
        verbose_logger=DummyVerboseLogger(),
        MODEL="gpt-3.5-turbo",
        pal_verbose=True,  # TODO
    ):
        self.llm = llm
        self.name = name
        self.description = description
        self.shared_memory = shared_memory
        self.action_planner = ActionPlanner(description, ACTION_PLAN_DESCRIPTION, llm)
        self.num_runs = num_runs
        self.belief = Belief()
        self.verbose_logger = verbose_logger
        openai.api_key = os.getenv("OPENAI_API_KEY")
        interface = pal.interface.ProgramInterface(
            model=MODEL, get_answer_expr="solution()", verbose=pal_verbose
        )

        interface.run_with_dict = types.MethodType(run_with_dict, interface)

        self.interface = interface

    def create_actions(self) -> List[BaseAction]:
        return [
            Deliberation(self.description, self.llm),
            GoogleSearch(self.description, self.belief.current_task, self.llm),
        ]

    def synthesize_output(self) -> str:
        synthesize_action = SynthesizeOutput(self.description, self.llm)
        result = synthesize_action.execute(
            self.belief.current_task.content,
            self.belief.get_context(self.llm.get_num_tokens),
            self.belief.get_internal_history(self.llm.get_num_tokens),
        )

        return result

    def answer_arithmetic(self, question, placeholder=False) -> str:
        if not placeholder:
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
