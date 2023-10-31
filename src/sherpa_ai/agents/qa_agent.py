from typing import List

from langchain.base_language import BaseLanguageModel

from sherpa_ai.action_planner import ActionPlanner
from sherpa_ai.actions import Deliberation, GoogleSearch, SynthesizeOutput
from sherpa_ai.actions.base import BaseAction
from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.memory import Belief
from sherpa_ai.memory.shared_memory import SharedMemory
from sherpa_ai.verbose_loggers.verbose_loggers import DummyVerboseLogger

# TODO: QA Agent only contains partial implementation from the original
# task agent, more investigation is needed to add more content to it.
# Some of the feature may be added to the agent base class, such as
# the verbose logger.

ACTION_PLAN_DESCRIPTION = "Given your specialized expertise, historical context, and your mission to facilitate Machine-Learning-based solutions, determine which action and its corresponding arguments would be the most scientifically sound and efficient approach to achieve the described task."  # noqa: E501

TASK_AGENT_DESRIPTION = "You are a **question answering assistant** who solves user questions and offers a detailed solution."  # noqa: E501


class QAAgent(BaseAgent):
    """
    The task agent is the agent handles a single task.
    """

    def __init__(
        self,
        llm: BaseLanguageModel,
        name: str = "QA Agent",
        description: str = TASK_AGENT_DESRIPTION,
        shared_memory: SharedMemory = None,
        belief: Belief = Belief(),
        num_runs: int = 3,
        verbose_logger=DummyVerboseLogger(),
    ):
        """
        The QA agent is the agent handles a single task.

        Args:
            llm (BaseLanguageModel): The language model used to generate text
            name (str, optional): The name of the agent. Defaults to "QA Agent".
            description (str, optional): The description of the agent. Defaults
                to TASK_AGENT_DESRIPTION.
            shared_memory (SharedMemory, optional): The shared memory used to
                store the context shared with all other agents. Defaults to None.
            belief (Belief, optional): The belief of the agent. Defaults to Belief().
            num_runs (int, optional): The number of runs the agent will run. Defaults
                to 3.
            verbose_logger (BaseVerboseLogger, optional): The verbose logger used to
                log the agent's internal state. Defaults to DummyVerboseLogger().
        """
        self.name = name
        self.description = description
        self.shared_memory = shared_memory
        self.belief = belief
        self.num_runs = num_runs
        self.llm = llm
        self.action_planner = ActionPlanner(description, ACTION_PLAN_DESCRIPTION, llm)
        self.verbose_logger = verbose_logger

    def create_actions(self) -> List[BaseAction]:
        return [
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
