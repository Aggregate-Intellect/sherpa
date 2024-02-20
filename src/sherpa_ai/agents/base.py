from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List

from loguru import logger

from sherpa_ai.action_planner import ActionPlanner
from sherpa_ai.actions.base import BaseAction
from sherpa_ai.events import EventType
from sherpa_ai.output_parsers.base import BaseOutputProcessor
from sherpa_ai.verbose_loggers.base import BaseVerboseLogger
from sherpa_ai.verbose_loggers.verbose_loggers import DummyVerboseLogger

# Avoid circular import
if TYPE_CHECKING:
    from sherpa_ai.memory import Belief, SharedMemory


class BaseAgent(ABC):
    def __init__(
        self,
        name: str,
        description: str,
        shared_memory: SharedMemory = None,
        belief: Belief = None,
        action_planner: ActionPlanner = None,
        num_runs: int = 1,
        verbose_logger: BaseVerboseLogger = DummyVerboseLogger(),
        actions: List[BaseAction] = [],
        validation_steps: int = 1,
        validations: List[BaseOutputProcessor] = [],
        feedback_agent_name: str = "critic",
    ):
        self.name = name
        self.description = description
        self.shared_memory = shared_memory
        self.belief = belief
        self.action_planner = action_planner
        self.num_runs = num_runs

        self.subscribed_events = []

        self.verbose_logger = verbose_logger
        self.actions = actions
        self.validation_steps = validation_steps
        self.validations = validations
        self.feedback_agent_name = feedback_agent_name

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

        actions = self.actions if len(self.actions) > 0 else self.create_actions()
        self.belief.set_actions(actions)

        for _ in range(self.num_runs):
            result = self.action_planner.select_action(self.belief)
            logger.info(f"Action selected: {result}")

            if result is None:
                # this means the action selector choose to finish
                break

            action_name, inputs = result
            action = self.belief.get_action(action_name)

            self.verbose_logger.log(
                f"```🤖{self.name} is executing {action_name}\n Input: {inputs}...```"
            )
            logger.debug(f"🤖{self.name} is executing {action_name}...```")

            self.belief.update_internal(
                EventType.action, self.name, action_name + str(inputs)
            )

            if action is None:
                logger.error(f"Action {action_name} not found")
                continue

            action_output = self.act(action, inputs)

            self.verbose_logger.log(f"```Action output: {action_output}```")
            logger.debug(f"```Action output: {action_output}```")

            self.belief.update_internal(
                EventType.action_output, self.name, action_output
            )

        result = self.validate_output()

        logger.debug(f"```🤖{self.name} wrote: {result}```")

        self.shared_memory.add(EventType.result, self.name, result)
        return result

    def validate_output(self):
        last_failed_validation = None

        for _ in range(self.validation_steps):
            result = self.synthesize_output()
            self.belief.update_internal(EventType.result, self.name, result)
            is_valid = True
            for validation in self.validations:
                validation_result = validation.process_output(result, self.belief)

                if not validation_result.is_valid:
                    is_valid = False
                    self.belief.update_internal(
                        EventType.feedback,
                        self.feedback_agent_name,
                        validation_result.feedback,
                    )
                    last_failed_validation = validation
                    break
                result = validation_result.result
            if is_valid:
                return result

        if last_failed_validation is not None:
            # if the validation failed after all steps, append the error messages to the result
            result = result + "\n" + last_failed_validation.get_failure_message()
        self.belief.update_internal(EventType.result, self.name, result)
        return result

    def observe(self):
        return self.shared_memory.observe(self.belief)

    def act(self, action, inputs):
        return action.execute(**inputs)
