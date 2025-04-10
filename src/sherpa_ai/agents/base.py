from __future__ import annotations

import asyncio
import asyncio.runners
import traceback
from abc import ABC, abstractmethod
from typing import Any, Callable, List, Optional, Union

from loguru import logger
from pydantic import BaseModel, ConfigDict

from sherpa_ai.actions.base import BaseAction
from sherpa_ai.actions.exceptions import (
    SherpaActionExecutionException,
    SherpaMissingInformationException,
)
from sherpa_ai.config.task_result import TaskResult
from sherpa_ai.memory import Belief, SharedMemory
from sherpa_ai.output_parsers.base import BaseOutputProcessor
from sherpa_ai.policies.base import BasePolicy, PolicyOutput
from sherpa_ai.policies.exceptions import SherpaPolicyException
from sherpa_ai.prompts.prompt_template_loader import PromptTemplate
from sherpa_ai.utils import is_coroutine_function


class BaseAgent(ABC, BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    name: str
    description: str
    shared_memory: SharedMemory = None
    belief: Belief = None
    policy: BasePolicy = None
    num_runs: int = 1
    actions: List[BaseAction] = []
    validation_steps: int = 1
    validations: List[BaseOutputProcessor] = []
    feedback_agent_name: str = "critic"
    global_regen_max: int = 12
    llm: Any = None
    prompt_template: PromptTemplate = None

    # Checks whether the execution of the agent should be stopped
    # default to never stop
    stop_checker: Callable[[Belief], bool] = lambda _: False

    if prompt_template is None:
        prompt_template = PromptTemplate("prompts/prompts.json")

    @abstractmethod
    def create_actions(self) -> List[BaseAction]:
        pass

    @abstractmethod
    def synthesize_output(self) -> str:
        pass

    def send_event(self, event: str, args: dict):
        """
        Send an event to the state machine in the belief

        Args:
            event (str): The event name
            args (dict): The arguments for the event
        """
        if self.belief.state_machine is None:
            logger.error("State machine is not defined in the belief")
            return

        getattr(self.belief.state_machine, event)(**args)

    async def async_send_event(self, event: str, args: dict):
        """
        Send an event to the state machine in the belief

        Args:
            event (str): The event name
            args (dict): The arguments for the event
        """
        if self.belief.state_machine is None:
            logger.error("State machine is not defined in the belief")
            return

        func = getattr(self.belief.state_machine, event)

        if func is None:
            logger.error(f"Event {event} is not defined in the state machine")
            return

        await func(**args)

    def agent_preparation(self):
        logger.debug(f"```⏳{self.name} is thinking...```")

        if self.shared_memory is not None:
            self.shared_memory.observe(self.belief)

        if len(self.belief.get_actions()) == 0:
            actions = self.actions if len(self.actions) > 0 else self.create_actions()
            self.belief.set_actions(actions)

    def select_action(self) -> Optional[PolicyOutput]:
        try:
            result = self.policy.select_action(self.belief)
            return result
        except SherpaPolicyException as e:
            self.belief.update_internal(
                "action_start",
                self.feedback_agent_name,
                outputs=f"Error in selecting action: {e}",
            )
            logger.exception(e)
            return None
        except Exception as e:
            logger.exception(e)
            return e

    async def async_select_action(self) -> Optional[PolicyOutput]:
        try:
            result = await self.policy.async_select_action(self.belief)
            return result
        except SherpaPolicyException as e:
            self.belief.update_internal(
                "action_finish",
                self.feedback_agent_name,
                outputs=f"Error in selecting action: {e}",
            )
            logger.exception(e)
            return None
        except Exception as e:
            logger.exception(e)
            return e

    def agent_finished(self, result: str) -> str:
        if len(self.validations) > 0:
            result = self.validate_output()

        logger.debug(f"```🤖{self.name} wrote: {result}```")

        if self.shared_memory is not None:
            self.shared_memory.add("result", self.name, content=result)
        return result

    def run(self) -> TaskResult:
        return asyncio.run(self.async_run())

    async def async_run(self) -> TaskResult:
        logger.debug(f"```⏳{self.name} is thinking...```")

        if self.shared_memory is not None:
            self.shared_memory.observe(self.belief)

        actions = await self.belief.async_get_actions()

        if len(actions) == 0:
            actions = self.actions if len(self.actions) > 0 else self.create_actions()
            self.belief.set_actions(actions)

        for _ in range(self.num_runs):
            actions = await self.belief.async_get_actions()
            if len(actions) == 0:
                break

            result = await self.async_select_action()

            if result is None:
                # this means no action is selected
                continue
            elif isinstance(result, Exception):
                tb_exception = traceback.TracebackException.from_exception(result)
                stack_trace = "".join(tb_exception.format())
                task_result = TaskResult(content=stack_trace, status="failed")
                return task_result

            logger.debug(f"Action selected: {result}")
            logger.debug(
                f"🤖{self.name} is executing```" "``` {result.action.name}...```"
            )

            action_output = await self.async_act(result.action, result.args)
            if action_output is None:
                continue
            elif isinstance(action_output, SherpaMissingInformationException):
                question = action_output.message
                task_result = TaskResult(content=question, status="waiting")
                return task_result

            action_output = self.belief.get(result.action.name, action_output)

            if self.stop_checker(self.belief):
                task_result = TaskResult(content=action_output, status="waiting")
                return task_result

            logger.debug(f"```Action output: {action_output}```")

        action_output = self.agent_finished(action_output)
        task_result = TaskResult(content=action_output, status="success")
        return task_result

    # The validation_iterator function is responsible for iterating through each
    # instantiated validation in the 'self.validations' list.
    # It performs the necessary validation steps for each validation, updating the
    # belief system and synthesizing output if needed.
    # It keeps track of the global regeneration count, whether all validations have
    # passed, and if any validation has been escaped.
    # The function returns the updated global regeneration count, the status of all
    # validations, whether any validation has been escaped, and the synthesized output.
    def validation_iterator(
        self,
        validations,
        global_regen_count,
        all_pass,
        validation_is_scaped,
        result,
    ):
        for i in range(len(validations)):
            validation = validations[i]
            logger.info(f"validation_running: {validation.__class__.__name__}")
            logger.info(f"validation_count: {validation.count}")
            # this checks if the validator has already exceeded the validation steps
            # limit.
            if validation.count < self.validation_steps:
                self.belief.update_internal("result", self.name, content=result)
                validation_result = validation.process_output(
                    text=result, belief=self.belief, llm=self.llm
                )
                logger.info(f"validation_result: {validation_result}")
                if not validation_result.is_valid:
                    self.belief.update_internal(
                        "feedback",
                        self.feedback_agent_name,
                        content=validation_result.feedback,
                    )
                    result = self.synthesize_output()
                    global_regen_count += 1
                    break

                # if all validations passed then set all_pass to True
                elif i == len(validations) - 1:
                    result = validation_result.result
                    all_pass = True
                else:
                    result = validation_result.result
            # if validation is the last one and surpassed the validation steps limit
            # then finish the loop with all_pass and mention there is a scaped
            # validation.
            elif i == len(validations) - 1:
                validation_is_scaped = True
                all_pass = True

            else:
                # if the validation has already reached the validation steps limit then
                # continue to the next validation.
                validation_is_scaped = True
        return global_regen_count, all_pass, validation_is_scaped, result

    def validate_output(self):
        """
        Validate the synthesized output through a series of validation steps.

        This method iterates through each validation in the 'validations' list, and for
        each validation, it performs 'validation_steps' attempts to synthesize output
        using 'synthesize_output' method. If the output doesn't pass validation,
        feedback is incorporated into the belief system.

        If a validation fails after all attempts, the error messages from the last
        failed validation are appended to the final result.

        Returns:
            str: The synthesized output after validation.
        """
        result = ""
        # create array of instance of validation so that we can keep track of how many
        # times regeneration happened.
        all_pass = False
        validation_is_scaped = False
        iteration_count = 0
        result = self.synthesize_output()
        global_regen_count = 0

        # reset the state of all the validation before starting the validation process.
        for validation in self.validations:
            validation.reset_state()

        validations = self.validations

        # this loop will run until max regeneration reached or all validations have
        # failed
        while self.global_regen_max > global_regen_count and not all_pass:
            logger.info(f"validations_size: {len(validations)}")
            iteration_count += 1
            logger.info(f"main_iteration: {iteration_count}")
            logger.info(f"regen_count: {global_regen_count}")
            logger.info("result: " + result)
            (
                global_regen_count,
                all_pass,
                validation_is_scaped,
                result,
            ) = self.validation_iterator(
                all_pass=all_pass,
                global_regen_count=global_regen_count,
                validation_is_scaped=validation_is_scaped,
                validations=validations,
                result=result,
            )
        # if all didn't pass or validation reached max regeneration run the validation
        # one more time but no regeneration.
        if validation_is_scaped or self.global_regen_max >= global_regen_count:
            failed_validations = []

            for validation in validations:
                validation_result = validation.process_output(
                    text=result, belief=self.belief, llm=self.llm
                )
                if not validation_result.is_valid:
                    failed_validations.append(validation)
                else:
                    result = validation_result.result

            result += "\n".join(
                failed_validation.get_failure_message()
                for failed_validation in failed_validations
            )

        else:
            # check if validation is not passed after all the attempts if so return the
            # error message.
            result += "\n".join(
                (
                    inst_val.get_failure_message()
                    if inst_val.count == self.validation_steps
                    else ""
                )
                for inst_val in validations
            )

        self.belief.update_internal("result", self.name, content=result)
        return result

    def observe(self):
        return self.shared_memory.observe(self.belief)

    def act(self, action: BaseAction, inputs: dict) -> Union[Optional[str], Exception]:
        asyncio.run(self.async_act(action, inputs))

    async def async_act(self, action: BaseAction, inputs: dict) -> Optional[str]:
        try:
            if is_coroutine_function(action):
                action_output = await action(**inputs)
            else:
                action_output = action(**inputs)

            return action_output
        except SherpaActionExecutionException as e:
            self.belief.update_internal(
                "action_finish",
                self.feedback_agent_name,
                outputs=f"Error in executing action: {action.name}. Error: {e}",
            )
            return None
