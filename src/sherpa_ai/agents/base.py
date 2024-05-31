from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional

from loguru import logger

from sherpa_ai.actions.base import BaseAction, BaseRetrievalAction
from sherpa_ai.events import EventType
from sherpa_ai.output_parsers.base import BaseOutputProcessor
from sherpa_ai.policies.base import BasePolicy
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
        policy: Optional[BasePolicy] = None,
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
        self.policy = policy
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
            result = self.policy.select_action(self.belief)
            logger.info(f"Action selected: {result}")

            if result is None:
                # this means no action is selected
                continue

            self.verbose_logger.log(
                f"```🤖{self.name} is executing {result.action.name}\n Input: {result.args}...```"
            )
            logger.debug(f"🤖{self.name} is executing {result.action.name}...```")

            self.belief.update_internal(
                EventType.action, self.name, result.action.name + str(result.args)
            )

            action_output = self.act(result.action, result.args)

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
        """
        Validate the synthesized output through a series of validation steps.

        This method iterates through each validation in the 'validations' list, and for each validation,
        it performs 'validation_steps' attempts to synthesize output using 'synthesize_output' method.
        If the output doesn't pass validation, feedback is incorporated into the belief system.

        If a validation fails after all attempts, the error messages from the last failed validation
        are appended to the final result.

        Returns:
            str: The synthesized output after validation.
        """
        failed_validation = []
        result = self.synthesize_output()
        for validation in self.validations:
            for count in range(self.validation_steps):
                self.belief.update_internal(EventType.result, self.name, result)

                validation_result = validation.process_output(
                    text=result, belief=self.belief, iteration_count=count
                )

                if validation_result.is_valid:
                    result = validation_result.result
                    break
                else:
                    self.belief.update_internal(
                        EventType.feedback,
                        self.feedback_agent_name,
                        validation_result.feedback,
                    )
                    result = self.synthesize_output()

            if count >= self.validation_steps:
                failed_validation.append(validation)

        if len(failed_validation) > 0:
            # if the validation failed after all steps, append the error messages to the result
            result += "\n".join(
                failed_validation.get_failure_message()
                for failed_validation in failed_validation
            )

        self.belief.update_internal(EventType.result, self.name, result)
        return result

    def observe(self):
        return self.shared_memory.observe(self.belief)

    def act(self, action, inputs):
        return action.execute(**inputs)
