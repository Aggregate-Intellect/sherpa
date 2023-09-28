from langchain.base_language import BaseLanguageModel
from loguru import logger

from sherpa_ai.action_planner import ActionPlanner
from sherpa_ai.actions import Deliberation, GoogleSearch, SynthesizeOutput
from sherpa_ai.agents.base import BaseAgent
from sherpa_ai.memory import Belief, EventType, SharedMemory

PHYSICIST_DESCRIPTION = "You are a physicist with a deep-rooted expertise in understanding and analyzing the fundamental principles of the universe, spanning from the tiniest subatomic particles to vast cosmic phenomena. Your primary role is to assist individuals, organizations, and researchers in navigating and resolving complex physics-related challenges, using your knowledge to guide decisions and ensure the accuracy and reliability of outcomes."  # noqa: E501

ACTION_PLAN_DESCRIPTION = "Given your specialized expertise, historical context, and your mission to facilitate physics-based solutions, determine which action and its corresponding arguments would be the most scientifically sound and efficient approach to achieve the described task."  # noqa: E501


class Physicist(BaseAgent):
    """
    The physicist agent answers questions or research about physics-related topics
    """

    def __init__(
        self,
        llm: BaseLanguageModel,
        name="Physicist",
        description=PHYSICIST_DESCRIPTION,
        shared_memory: SharedMemory = None,
        num_runs=3,
    ):
        self.llm = llm
        self.name = name
        self.description = description
        self.shared_memory = shared_memory
        self.action_planner = ActionPlanner(description, ACTION_PLAN_DESCRIPTION, llm)
        self.num_runs = num_runs
        self.belief = Belief()

    def run(self):
        self.shared_memory.observe(self.belief)

        actions = [
            Deliberation(self.description, self.llm),
            GoogleSearch(self.description, self.belief.current_task, self.llm),
        ]

        self.belief.set_actions(actions)

        for _ in range(self.num_runs):
            result = self.action_planner.select_action(self.belief)

            if result is None:
                # this means the action selector choose to finish
                break

            action_name, inputs = result
            action = self.belief.get_action(action_name)

            self.belief.update_internal(
                EventType.action, self.name, action_name + str(inputs)
            )

            if action is None:
                logger.error(f"Action {action_name} not found")
                continue

            action_output = self.act(action, inputs)
            self.belief.update_internal(
                EventType.action_output, self.name, action_output
            )

        synthesize_action = SynthesizeOutput(self.description, self.llm)
        result = synthesize_action.run(self.belief)

        self.shared_memory.add(EventType.result, self.name, result)
        return result
