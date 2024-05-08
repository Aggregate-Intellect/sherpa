from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional

from loguru import logger

from sherpa_ai.actions.base import BaseAction
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
        global_regen_max: int = 12,
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
        self.global_regen_max = global_regen_max
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
        result = ""
        # create array of instance of validation so that we can keep track of how many times regeneration happened.
        instantiated_validations = [validation() for validation in self.validations]

        all_pass = False
        validation_is_scaped = False
        while_count = 0
        # this loop will run until max regeneration reached or all validations have failed
        while (
            self.global_regen_max > sum(val.count for val in instantiated_validations)
            and not all_pass
        ):
            break_while = False
            if break_while:
                break
            while_count += 1
            logger.info(f"main_iteration: {while_count}")
            logger.info(
                f"regen_count: {sum(val.count for val in instantiated_validations)}"
            )
            for x in range(len(instantiated_validations)):
                validation = instantiated_validations[x]
                logger.info(f"validation_running: {validation.__class__.__name__}")
                logger.info(f"validation_count: {validation.count}")
                if validation.count < self.validation_steps:
                    result = self.synthesize_output()
                    self.belief.update_internal(EventType.result, self.name, result)
                    validation_result = validation.process_output(
                        text=result, belief=self.belief
                    )
                    logger.info(f"validation_result: {validation_result.is_valid}")
                    if not validation_result.is_valid:
                        self.belief.update_internal(
                            EventType.feedback,
                            self.feedback_agent_name,
                            validation_result.feedback,
                        )
                        break
                    elif x == len(instantiated_validations) - 1:
                        all_pass = True
                elif x == len(instantiated_validations) - 1:
                    validation_is_scaped = True
                    all_pass = True
                else:
                    validation_is_scaped = True

        # if all didn't pass and reached max regeneration run the validation one more time but no regeneration.
        if validation_is_scaped or self.global_regen_max >= sum(
            val.count for val in instantiated_validations
        ):
            failed_validations = []

            for validation in self.validations:
                _validation = validation()
                validation_result = _validation.process_output(
                    text=result, belief=self.belief
                )
                if not validation_result.is_valid:
                    failed_validations.append(_validation)

            result += "\n".join(
                failed_validation.get_failure_message()
                for failed_validation in failed_validations
            )

        else:
            result += "\n".join(
                (
                    inst_val.get_failure_message()
                    if inst_val.count == self.validation_steps
                    else ""
                )
                for inst_val in instantiated_validations
            )

        self.belief.update_internal(EventType.result, self.name, result)
        return result

    def observe(self):
        return self.shared_memory.observe(self.belief)

    def act(self, action, inputs):
        return action.execute(**inputs)
