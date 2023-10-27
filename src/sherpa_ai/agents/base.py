from abc import ABC, abstractmethod
from typing import List

from loguru import logger

from sherpa_ai.actions.base import BaseAction
from sherpa_ai.events import EventType
from sherpa_ai.verbose_loggers.base import BaseVerboseLogger
from sherpa_ai.verbose_loggers.verbose_loggers import DummyVerboseLogger


class BaseAgent(ABC):
    def __init__(
        self,
        name: str,
        description: str,
        shared_memory=None,
        belief=None,
        action_selector=None,
        num_runs=1,
        verbose_logger: BaseVerboseLogger = DummyVerboseLogger(),
    ):
        self.name = name
        self.description = description
        self.shared_memory = shared_memory
        self.belief = belief
        self.action_selector = action_selector
        self.num_runs = num_runs

        self.actions = []
        self.reflections = []
        self.subscribed_events = []

        self.verbose_logger = verbose_logger

    def add_action(self, action):
        self.actions.append(action)

    def add_reflection(self, reflection):
        self.reflections.append(reflection)

    @abstractmethod
    def create_actions(self) -> List[BaseAction]:
        pass

    @abstractmethod
    def synthesize_output(self) -> str:
        pass

    def run(self):
        self.verbose_logger.log(f"⏳{self.name} is thinking...")
        logger.debug(f"```⏳{self.name} is thinking...```")

        self.shared_memory.observe(self.belief)

        actions = self.create_actions()
        self.belief.set_actions(actions)

        for _ in range(self.num_runs):
            result = self.action_planner.select_action(self.belief)
            logger.info(f"Action selected: {result}")

            if result is None:
                # this means the action selector choose to finish
                break

            action_name, inputs = result
            action = self.belief.get_action(action_name)

            self.verbose_logger.log(f"🤖{self.name} is executing {action_name}...")
            logger.debug(f"```🤖{self.name} is executing {action_name}...```")

            self.belief.update_internal(
                EventType.action, self.name, action_name + str(inputs)
            )

            if action is None:
                logger.error(f"Action {action_name} not found")
                continue

            action_output = self.act(action, inputs)

            self.verbose_logger.log(f"Action output: {action_output}")
            logger.debug(f"```Action output: {action_output}```")

            self.belief.update_internal(
                EventType.action_output, self.name, action_output
            )

        result = self.synthesize_output()

        self.verbose_logger.log(f"🤖{self.name} wrote: {result}")
        logger.debug(f"```🤖{self.name} wrote: {result}```")

        self.shared_memory.add(EventType.result, self.name, result)
        return result

    def observe(self):
        return self.shared_memory.observe(self.belief)

    def act(self, action, inputs):
        return action.execute(**inputs)
