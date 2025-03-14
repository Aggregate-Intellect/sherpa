from typing import List, Optional

from langchain_core.language_models import BaseChatModel 
from loguru import logger 

from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.events import EventType
from sherpa_ai.memory import Belief, SharedMemory
from sherpa_ai.verbose_loggers.verbose_loggers import DummyVerboseLogger


DESCRIPTION_PROMPT = """
You are a Critic agent that receive a plan from the planner to execuate a task from user.
Your goal is to output the {} most necessary feedback given the corrent plan to solve the task.
"""  # noqa: E501
IMPORTANCE_PROMPT = """The plan you should be necessary and important to complete the task.
Evaluate if the content of plan and selected actions/ tools are important and necessary.
Output format:
Score: <Integer score from 1 - 10>
Evaluation: <evaluation in text>
Do not include other text in your resonse.
Output:
"""  # noqa: E501
DETAIL_PROMPT = """The plan you should be detailed enough to complete the task.
Evaluate if the content of plan and selected actions/ tools contains all the details the task needed.
Output format:
Score: <Integer score from 1 - 10>
Evaluation: <evaluation in text>
Do not include other text in your resonse.
Output:
"""  # noqa: E501
INSIGHT_PROMPT = """
What are the top 5 high-level insights you can infer from the all the memory you have?
Only output insights with high confidence.
Insight:
"""  # noqa: E501
FEEDBACK_PROMPT = """
What are the {} most important feedback for the plan received from the planner, using the\
insight you have from current observation, evaluation using the importance matrices and detail matrices.
Feedback:
"""  # noqa: E501


class Critic(BaseAgent):
    """
    The critic agent receives a plan from the planner and evaluate the plan based on
    some pre-defined metrics. At the same time, it gives the feedback to the planner.
    """

    def __init__(
        self,
        llm: BaseChatModel,
        description: str = DESCRIPTION_PROMPT,
        shared_memory: Optional[SharedMemory] = None,
        belief: Belief = Belief(),
        ratio: float = 0.9,
        num_feedback: int = 3,
        verbose_logger=DummyVerboseLogger(),
    ):
        self.name = "Critic"
        self.llm = llm
        self.description = description
        self.shared_memory = shared_memory
        self.belief = belief
        self.ratio = ratio
        self.num_feedback = num_feedback
        self.verbose_logger = verbose_logger

    def get_importance_evaluation(self, task: str, plan: str):
        # return score in int and evaluation in string for importance matrix
        prompt = "Task: " + task + "\nPlan: " + plan + IMPORTANCE_PROMPT
        output = self.llm.predict(prompt)
        score = int(output.split("Score:")[1].split("Evaluation")[0])
        evaluation = output.split("Evaluation: ")[1]
        return score, evaluation

    def get_detail_evaluation(self, task: str, plan: str):
        # return score in int and evaluation in string for detail matrix
        prompt = "Task: " + task + "\nPlan: " + plan + DETAIL_PROMPT
        output = self.llm.predict(prompt)
        score = int(output.split("Score:")[1].split("Evaluation")[0])
        evaluation = output.split("Evaluation: ")[1]
        return score, evaluation

    def get_insight(self):
        # return a list of string: top 5 important insight given the belief and memory
        # (observation)
        observation = self.observe(self.belief)
        prompt = "Observation: " + observation + "\n" + INSIGHT_PROMPT
        result = self.llm.predict(prompt)
        insights = [i for i in result.split("\n") if len(i.strip()) > 0][:5]
        return insights

    def post_process(self, feedback: str):
        return [i for i in feedback.split("\n") if i]

    def get_feedback(self, task: str, plan: str) -> List[str]:
        # observation = self.observe(self.belief)
        i_score, i_evaluation = self.get_importance_evaluation(task, plan)
        d_score, d_evaluation = self.get_detail_evaluation(task, plan)
        # approve or not, check score/ ratio
        # insights = self.get_insight()

        logger.info(f"i_score: {i_score}, d_score: {d_score}")

        if i_score < 10 * self.ratio or d_score < 10 * self.ratio:
            prompt = (
                # f"\nCurrent observation you have is: {observation}"
                # f"Insight you have from current observation: {insights}"
                f"Task: {task}"
                f"Evaluation in the importance matrices: {i_evaluation}"
                f"Evaluation in the detail matrices: {d_evaluation}"
                + FEEDBACK_PROMPT.format(self.num_feedback)
            )
            feedback = self.llm.predict(self.description + prompt)

            self.shared_memory.add(EventType.feedback, self.name, feedback)
            logger.info(f"feedback: {feedback}")

            return self.post_process(feedback)
        else:
            return ""

    def create_actions(self):
        pass

    def synthesize_output(self) -> str:
        pass
