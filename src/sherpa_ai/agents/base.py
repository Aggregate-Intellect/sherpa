from __future__ import annotations

import asyncio
import asyncio.runners
import traceback
from abc import ABC, abstractmethod
from typing import Any, Callable, List, Optional, Union

from loguru import logger
from pydantic import BaseModel, ConfigDict
from langchain_core.language_models.base import BaseLanguageModel

from sherpa_ai.actions.base import BaseAction
from sherpa_ai.actions.exceptions import (
    SherpaActionExecutionException,
    SherpaMissingInformationException,
)
from sherpa_ai.config.task_result import TaskResult
from sherpa_ai.events import Event
from sherpa_ai.memory import Belief, SharedMemory
from sherpa_ai.output_parsers.base import BaseOutputProcessor
from sherpa_ai.policies.base import BasePolicy, PolicyOutput
from sherpa_ai.policies.exceptions import SherpaPolicyException
from sherpa_ai.prompts.prompt_template_loader import PromptTemplate
from sherpa_ai.utils import is_coroutine_function


class BaseAgent(ABC, BaseModel):
    """Base class for all agents in the Sherpa AI system.

    This abstract class defines the core functionality and interface that all agents
    must implement. It provides methods for action selection, execution, validation,
    and output synthesis.

    Attributes:
        name (str): The name of the agent.
        description (str): A description of the agent's purpose and capabilities.
        shared_memory (SharedMemory): Memory shared between agents for information exchange.
        belief (Belief): The agent's internal state and knowledge.
        policy (BasePolicy): The policy that determines which actions to take.
        num_runs (int): Number of action execution cycles to perform. Defaults to 1.
        actions (List[BaseAction]): List of actions the agent can perform.
        validation_steps (int): Number of validation attempts per validation. Defaults to 1.
        validations (List[BaseOutputProcessor]): List of output validators.
        feedback_agent_name (str): Name of the agent providing feedback. Defaults to "critic".
        global_regen_max (int): Maximum number of output regeneration attempts. Defaults to 12.
        llm (Any): Language model used for text generation.
        prompt_template (PromptTemplate): Template for generating prompts.
        stop_checker (Callable[[Belief], bool]): Function to determine if execution should stop.

    Example:
        >>> from sherpa_ai.agents.base import BaseAgent
        >>> from sherpa_ai.actions.base import BaseAction
        >>> class MyAgent(BaseAgent):
        ...     def create_actions(self) -> List[BaseAction]:
        ...         return []
        ...     def synthesize_output(self) -> str:
        ...         return "Output"
        >>> agent = MyAgent(name="TestAgent", description="A test agent")
        >>> print(agent.name)
        TestAgent
    """  # noqa: E501

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
    llm: Optional[BaseLanguageModel] = None
    prompt_template: PromptTemplate = None

    # Checks whether the execution of the agent should be stopped
    # default to never stop
    stop_checker: Callable[[Belief], bool] = lambda _: False

    if prompt_template is None:
        prompt_template = PromptTemplate("prompts/prompts.json")

    @abstractmethod
    def create_actions(self) -> List[BaseAction]:
        """Create and return the list of actions available to this agent.

        This method must be implemented by all agent subclasses to define
        the specific actions that the agent can perform.

        Returns:
            List[BaseAction]: List of action objects that the agent can use.

        Example:
            >>> from sherpa_ai.agents.base import BaseAgent
            >>> from sherpa_ai.actions.base import BaseAction
            >>> class MyAgent(BaseAgent):
            ...     def create_actions(self) -> List[BaseAction]:
            ...         return [MyCustomAction()]
            ...     def synthesize_output(self) -> str:
            ...         return "Output"
            >>> agent = MyAgent(name="TestAgent", description="A test agent")
            >>> actions = agent.create_actions()
            >>> print(len(actions))
            1
        """
        pass

    @abstractmethod
    def synthesize_output(self) -> str:
        """Generate the final output based on the agent's actions and belief state.

        This method must be implemented by all agent subclasses to define
        how the agent produces its final output from its internal state.

        Returns:
            str: The synthesized output string.

        Example:
            >>> from sherpa_ai.agents.base import BaseAgent
            >>> class MyAgent(BaseAgent):
            ...     def create_actions(self) -> List[BaseAction]:
            ...         return []
            ...     def synthesize_output(self) -> str:
            ...         return "This is my final answer."
            >>> agent = MyAgent(name="TestAgent", description="A test agent")
            >>> output = agent.synthesize_output()
            >>> print(output)
            This is my final answer.
        """
        pass

    def send_event(self, event: str, args: dict):
        """Send an event to the state machine in the belief.

        This method dispatches an event to the agent's belief state machine,
        allowing the agent to update its internal state based on external events.

        Args:
            event (str): The name of the event to send.
            args (dict): Arguments to pass to the event handler.

        Example:
            >>> from sherpa_ai.agents.base import BaseAgent
            >>> class MyAgent(BaseAgent):
            ...     def create_actions(self) -> List[BaseAction]:
            ...         return []
            ...     def synthesize_output(self) -> str:
            ...         return "Output"
            >>> agent = MyAgent(name="TestAgent", description="A test agent")
            >>> agent.send_event("task_start", {"task_id": "123"})
        """
        if self.belief.state_machine is None:
            logger.error("State machine is not defined in the belief")
            return

        getattr(self.belief.state_machine, event)(**args)

    async def async_send_event(self, event: str, args: dict):
        """Send an event to the state machine in the belief asynchronously.

        This method dispatches an event to the agent's belief state machine
        asynchronously, allowing for non-blocking state updates.

        Args:
            event (str): The name of the event to send.
            args (dict): Arguments to pass to the event handler.

        Example:
            >>> import asyncio
            >>> from sherpa_ai.agents.base import BaseAgent
            >>> class MyAgent(BaseAgent):
            ...     def create_actions(self) -> List[BaseAction]:
            ...         return []
            ...     def synthesize_output(self) -> str:
            ...         return "Output"
            >>> agent = MyAgent(name="TestAgent", description="A test agent")
            >>> asyncio.run(agent.async_send_event("task_start", {"task_id": "123"}))
        """
        if self.belief.state_machine is None:
            logger.error("State machine is not defined in the belief")
            return

        func = getattr(self.belief.state_machine, event)

        if func is None:
            logger.error(f"Event {event} is not defined in the state machine")
            return

        await func(**args)

    async def async_handle_event(self, event: Event):
        """Handle a specific type of event.

        This method processes the event based on its type and updates the agent's
        belief state accordingly. To create customized event handling,
        override this method in subclasses.

        Args:
            event (Event): The event to handle.
        """
        if event.event_type == "trigger":
            # explicit trigger event, send it to the state machine
            await self.async_send_event(event.name, event.args)
        else:
            # add the event to the belief
            self.belief.internal_events.append(event)

    def agent_preparation(self):
        """Prepare the agent for execution.

        This method initializes the agent's state, observes the shared memory,
        and sets up the agent's actions if they haven't been defined yet.

        Example:
            >>> from sherpa_ai.agents.base import BaseAgent
            >>> class MyAgent(BaseAgent):
            ...     def create_actions(self) -> List[BaseAction]:
            ...         return []
            ...     def synthesize_output(self) -> str:
            ...         return "Output"
            >>> agent = MyAgent(name="TestAgent", description="A test agent")
            >>> agent.agent_preparation()
        """
        logger.debug(f"```⏳{self.name} is thinking...```")

        if len(self.belief.get_actions()) == 0 and self.belief.state_machine is None:
            actions = self.actions if len(self.actions) > 0 else self.create_actions()
            self.belief.set_actions(actions)

    def select_action(self) -> Optional[PolicyOutput]:
        """Select the next action to execute based on the current belief state.

        This method uses the agent's policy to determine which action to take
        next based on the current state of the agent's belief.

        Returns:
            Optional[PolicyOutput]: The selected action and its arguments, or None if
                no action could be selected.

        Example:
            >>> from sherpa_ai.agents.base import BaseAgent
            >>> class MyAgent(BaseAgent):
            ...     def create_actions(self) -> List[BaseAction]:
            ...         return []
            ...     def synthesize_output(self) -> str:
            ...         return "Output"
            >>> agent = MyAgent(name="TestAgent", description="A test agent")
            >>> action = agent.select_action()
            >>> print(action is None)
            True
        """
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
        """Select the next action to execute asynchronously.

        This method uses the agent's policy to determine which action to take
        next based on the current state of the agent's belief, in an asynchronous manner.

        Returns:
            Optional[PolicyOutput]: The selected action and its arguments, or None if
                no action could be selected.

        Example:
            >>> import asyncio
            >>> from sherpa_ai.agents.base import BaseAgent
            >>> class MyAgent(BaseAgent):
            ...     def create_actions(self) -> List[BaseAction]:
            ...         return []
            ...     def synthesize_output(self) -> str:
            ...         return "Output"
            >>> agent = MyAgent(name="TestAgent", description="A test agent")
            >>> action = asyncio.run(agent.async_select_action())
            >>> print(action is None)
            True
        """  # noqa: E501
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

    async def agent_finished(self, result: str) -> str:
        """Process the final result after all actions have been executed.

        This method validates the output if validators are present, logs the result,
        and stores it in the shared memory.

        Args:
            result (str): The final result to process.

        Returns:
            str: The processed result.

        Example:
            >>> from sherpa_ai.agents.base import BaseAgent
            >>> class MyAgent(BaseAgent):
            ...     def create_actions(self) -> List[BaseAction]:
            ...         return []
            ...     def synthesize_output(self) -> str:
            ...         return "Output"
            >>> agent = MyAgent(name="TestAgent", description="A test agent")
            >>> final_result = agent.agent_finished("My answer")
            >>> print(final_result)
            My answer
        """
        if len(self.validations) > 0:
            result = self.validate_output()

        logger.debug(f"```🤖{self.name} wrote: {result}```")

        if self.shared_memory is not None:
            await self.shared_memory.async_add("result", self.name, content=result)
        return result

    def run(self) -> TaskResult:
        """Run the agent synchronously.

        This method executes the agent's action selection and execution loop
        synchronously, returning a TaskResult with the final output.

        Returns:
            TaskResult: The result of the agent's execution.

        Example:
            >>> from sherpa_ai.agents.base import BaseAgent
            >>> class MyAgent(BaseAgent):
            ...     def create_actions(self) -> List[BaseAction]:
            ...         return []
            ...     def synthesize_output(self) -> str:
            ...         return "Output"
            >>> agent = MyAgent(name="TestAgent", description="A test agent")
            >>> result = agent.run()
            >>> print(result.status)
            success
        """
        return asyncio.run(self.async_run())

    async def async_run(self) -> TaskResult:
        """Run the agent asynchronously.

        This method executes the agent's action selection and execution loop
        asynchronously, returning a TaskResult with the final output.

        Returns:
            TaskResult: The result of the agent's execution.

        Example:
            >>> import asyncio
            >>> from sherpa_ai.agents.base import BaseAgent
            >>> class MyAgent(BaseAgent):
            ...     def create_actions(self) -> List[BaseAction]:
            ...         return []
            ...     def synthesize_output(self) -> str:
            ...         return "Output"
            >>> agent = MyAgent(name="TestAgent", description="A test agent")
            >>> result = asyncio.run(agent.async_run())
            >>> print(result.status)
            success
        """
        logger.debug(f"```⏳{self.name} is thinking...```")

        actions = await self.belief.async_get_actions()

        if len(actions) == 0 and self.belief.state_machine is None:
            actions = self.actions if len(self.actions) > 0 else self.create_actions()
            self.belief.set_actions(actions)

        action_output = None
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

        action_output = await self.agent_finished(action_output)
        task_result = TaskResult(content=action_output, status="success")
        return task_result

    def validation_iterator(
        self,
        validations,
        global_regen_count,
        all_pass,
        validation_is_scaped,
        result,
    ):
        """Iterate through validations and process their results.

        This method processes each validation in sequence, updating the belief
        and regenerating output if necessary.

        Args:
            validations: List of validators to process.
            global_regen_count: Current count of regeneration attempts.
            all_pass: Whether all validations have passed so far.
            validation_is_scaped: Whether any validation has been skipped.
            result: Current result to validate.

        Returns:
            tuple: Updated values for global_regen_count, all_pass, validation_is_scaped, and result.

        Example:
            >>> from sherpa_ai.agents.base import BaseAgent
            >>> class MyAgent(BaseAgent):
            ...     def create_actions(self) -> List[BaseAction]:
            ...         return []
            ...     def synthesize_output(self) -> str:
            ...         return "Output"
            >>> agent = MyAgent(name="TestAgent", description="A test agent")
            >>> count, passed, escaped, output = agent.validation_iterator(
            ...     validations=[],
            ...     global_regen_count=0,
            ...     all_pass=False,
            ...     validation_is_scaped=False,
            ...     result="Test output"
            ... )
            >>> print(count)
            0
        """  # noqa: E501
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
        """Validate the synthesized output through a series of validation steps.

        This method iterates through each validation in the 'validations' list, and for
        each validation, it performs 'validation_steps' attempts to synthesize output
        using 'synthesize_output' method. If the output doesn't pass validation,
        feedback is incorporated into the belief system.

        If a validation fails after all attempts, the error messages from the last
        failed validation are appended to the final result.

        Returns:
            str: The synthesized output after validation.

        Example:
            >>> from sherpa_ai.agents.base import BaseAgent
            >>> class MyAgent(BaseAgent):
            ...     def create_actions(self) -> List[BaseAction]:
            ...         return []
            ...     def synthesize_output(self) -> str:
            ...         return "Validated output"
            >>> agent = MyAgent(name="TestAgent", description="A test agent")
            >>> result = agent.validate_output()
            >>> print(result)
            Validated output
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

    def act(self, action: BaseAction, inputs: dict) -> Union[Optional[str], Exception]:
        """Execute an action synchronously.

        This method executes the specified action with the given inputs,
        handling any exceptions that may occur during execution.

        Args:
            action (BaseAction): The action to execute.
            inputs (dict): Input parameters for the action.

        Returns:
            Union[Optional[str], Exception]: The result of the action execution,
                or an exception if execution failed.

        Example:
            >>> from sherpa_ai.agents.base import BaseAgent
            >>> from sherpa_ai.actions.base import BaseAction
            >>> class MyAction(BaseAction):
            ...     def execute(self, **kwargs):
            ...         return "Action executed"
            >>> class MyAgent(BaseAgent):
            ...     def create_actions(self) -> List[BaseAction]:
            ...         return [MyAction()]
            ...     def synthesize_output(self) -> str:
            ...         return "Output"
            >>> agent = MyAgent(name="TestAgent", description="A test agent")
            >>> result = agent.act(MyAction(), {"param": "value"})
            >>> print(result)
            Action executed
        """
        asyncio.run(self.async_act(action, inputs))

    async def async_act(self, action: BaseAction, inputs: dict) -> Optional[str]:
        """Execute an action asynchronously.

        This method executes the specified action with the given inputs asynchronously,
        handling any exceptions that may occur during execution.

        Args:
            action (BaseAction): The action to execute.
            inputs (dict): Input parameters for the action.

        Returns:
            Optional[str]: The result of the action execution, or None if execution failed.

        Example:
            >>> import asyncio
            >>> from sherpa_ai.agents.base import BaseAgent
            >>> from sherpa_ai.actions.base import BaseAction
            >>> class MyAction(BaseAction):
            ...     async def execute(self, **kwargs):
            ...         return "Action executed"
            >>> class MyAgent(BaseAgent):
            ...     def create_actions(self) -> List[BaseAction]:
            ...         return [MyAction()]
            ...     def synthesize_output(self) -> str:
            ...         return "Output"
            >>> agent = MyAgent(name="TestAgent", description="A test agent")
            >>> result = asyncio.run(agent.async_act(MyAction(), {"param": "value"}))
            >>> print(result)
            Action executed
        """  # noqa: E501
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

    def __hash__(self):
        """Make BaseAgent hashable based on its name.

        Returns:
            int: Hash value for the agent

        Example:
            >>> agent1 = MyAgent(name="Agent1", description="First agent")
            >>> agent2 = MyAgent(name="Agent2", description="Second agent")
            >>> agent_set = {agent1, agent2}
            >>> len(agent_set)
            2
        """
        return hash(self.name)

    def __eq__(self, other):
        """Define equality for BaseAgent based on name.

        Args:
            other: Object to compare with

        Returns:
            bool: True if the objects are equal, False otherwise

        Example:
            >>> agent1 = MyAgent(name="Agent", description="First instance")
            >>> agent2 = MyAgent(name="Agent", description="Second instance")
            >>> agent1 == agent2
            True
        """
        if not isinstance(other, BaseAgent):
            return False
        return self.name == other.name
