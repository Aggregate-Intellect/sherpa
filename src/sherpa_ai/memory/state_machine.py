"""State machine module for Sherpa AI.

This module provides state machine functionality for the Sherpa AI system.
It defines the SherpaStateMachine class which manages agent state transitions
and actions.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Optional, Union

import transitions as ts
from loguru import logger
from transitions.extensions.states import Tags, add_state_features

from sherpa_ai.memory.utils import StateDesc, TransitionDesc, add_transition_features
from sherpa_ai.utils import is_coroutine_function

if TYPE_CHECKING:
    from sherpa_ai.actions.base import BaseAction


class State(ts.State):
    """Extended state class for Sherpa state machine.

    This class extends the transitions library's State class to provide
    additional functionality for Sherpa's state machine implementation.
    """

    def __init__(self, *args, **kwargs):
        """Initialize a new State instance.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        super().__init__(*args, **kwargs)


class Transition(ts.Transition):
    """Extended transition class for Sherpa state machine.

    This class extends the transitions library's Transition class to provide
    additional functionality for Sherpa's state machine implementation.
    """

    def __init__(self, *args, **kwargs):
        """Initialize a new Transition instance.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        super().__init__(*args, **kwargs)


class SherpaStateMachine:
    """State machine for managing agent behavior in Sherpa AI.

    This class implements a state machine that defines the behavior of an agent
    by managing states and transitions between them. It provides functionality
    for adding transitions, executing actions, and managing state changes.

    Attributes:
        explicit_transitions (set): Set of triggers that are explicitly defined.
        sm (ts.Machine): The underlying state machine object.

    Example:
        >>> machine = SherpaStateMachine(
        ...     name="agent",
        ...     states=["idle", "working"],
        ...     transitions=[{"trigger": "start", "source": "idle", "dest": "working"}],
        ...     initial="idle"
        ... )
        >>> print(machine.state)
        'idle'
        >>> machine.start()
        >>> print(machine.state)
        'working'
    """

    explicit_transitions: set = set()
    sm: ts.Machine = None

    def __init__(
        self,
        name: str = "",
        states: list[Any] = [],
        transitions: list[Any] = [],
        initial: str = "",
        auto_transitions=False,
        sm_cls: type = ts.Machine,
        action_map: dict[str, BaseAction] = {},
    ):
        """Initialize the state machine.

        Args:
            name (str): Name of the state machine.
            states (list): List of states in the state machine.
            transitions (list): List of transitions connecting states.
            initial (str): Name of initial state.
            auto_transitions (bool): Whether to allow automatic transitions.
            sm_cls (type): State machine class to instantiate.
            action_map (dict): Mapping from action name to action object.

        Example:
            >>> machine = SherpaStateMachine(
            ...     name="agent",
            ...     states=["idle", "working"],
            ...     initial="idle"
            ... )
            >>> print(machine.state)
            'idle'
        """
        for name, action in action_map.items():
            self.__setattr__(name, action)

            # sm_cls.state_cls = State
            # sm_cls.transition_cls = Transition

        # extend the state machine states with additional features
        extend_states = add_state_features(Tags, StateDesc)
        extend_transitions = add_transition_features(TransitionDesc)

        sm_cls = extend_states(sm_cls)
        sm_cls = extend_transitions(sm_cls)

        self.sm = sm_cls(
            model=self,
            name=name,
            states=states,
            transitions=transitions,
            initial=initial,
            auto_transitions=auto_transitions,
        )

        self.add_explicit_transitions(transitions)

    def add_explicit_transitions(self, transitions: list[Any]):
        """Add explicit transitions to the state machine.

        Args:
            transitions (list): List of explicit transitions to add.

        Example:
            >>> machine = SherpaStateMachine()
            >>> transitions = [{"trigger": "start", "source": "idle", "dest": "working"}]
            >>> machine.add_explicit_transitions(transitions)
            >>> print("start" in machine.explicit_transitions)
            True
        """  # noqa: E501
        for t in transitions:
            if isinstance(t, dict):
                self.explicit_transitions.add(t["trigger"])
            elif isinstance(t, list):
                self.explicit_transitions.add(t[0])
            else:
                logger.warning(f"Invalid transition {t}")

    def update_transition(
        self,
        trigger: str,
        source: str,
        dest: str,
        conditions: Union[Callable, list[Callable]] = None,
        action: Optional[BaseAction] = None,
        **kwargs,
    ):
        """Update or add a transition to the state machine.

        Args:
            trigger (str): Trigger event for the transition.
            source (str): Source state name.
            dest (str): Destination state name.
            conditions (Union[Callable, list[Callable]]): Condition functions.
            action (Optional[BaseAction]): Action to execute before transition.
            **kwargs: Additional transition parameters.

        Example:
            >>> machine = SherpaStateMachine(states=["idle", "working"])
            >>> def check_condition(): return True
            >>> machine.update_transition(
            ...     "start", "idle", "working",
            ...     conditions=check_condition
            ... )
            >>> print("start" in machine.explicit_transitions)
            True
        """
        self.explicit_transitions.add(trigger)

        if len(self.sm.get_transitions(trigger, source, dest)) > 0:
            self.sm.remove_transition(trigger, source, dest)

        if action is not None:
            self.sm.add_transition(
                trigger=trigger,
                source=source,
                dest=dest,
                conditions=conditions,
                before=action,
                **kwargs,
            )
        else:
            self.sm.add_transition(
                trigger=trigger,
                source=source,
                dest=dest,
                conditions=conditions,
                **kwargs,
            )

    async def async_get_actions(
        self, include_waiting: bool = False
    ) -> list[BaseAction]:
        """Get available transitions as actions from current state.

        Args:
            include_waiting (bool): Whether to include waiting state transitions.

        Returns:
            list[BaseAction]: List of executable actions from current state.

        Example:
            >>> machine = SherpaStateMachine(states=["idle", "working"])
            >>> machine.update_transition("start", "idle", "working")
            >>> actions = await machine.async_get_actions()
            >>> print(len(actions))
            1
        """
        state = self.state
        state_obj = self.sm.get_state(state)

        if not include_waiting and state_obj.is_waiting:
            return []

        triggers = self.sm.get_triggers(state)
        actions = []

        for t in triggers:
            if t not in self.explicit_transitions:
                continue

            if is_coroutine_function(self.may_trigger):
                can_trigger = await self.may_trigger(t)
            else:
                can_trigger = self.may_trigger(t)
            if not can_trigger:
                continue

            event = self.sm.events.get(t)
            for source, transitions in event.transitions.items():
                if state.startswith(source):
                    transition = transitions[0]
                    action = self.transition_to_action(t, transition)
                    actions.append(action)

        return actions

    def get_actions(self, include_waiting: bool = False) -> list[BaseAction]:
        """Get available transitions as actions from current state.

        Args:
            include_waiting (bool): Whether to include waiting state transitions.

        Returns:
            list[BaseAction]: List of executable actions from current state.

        Example:
            >>> machine = SherpaStateMachine(states=["idle", "working"])
            >>> machine.update_transition("start", "idle", "working")
            >>> actions = machine.get_actions()
            >>> print(len(actions))
            1
        """
        if self.is_async():
            raise ValueError("Cannot get sync actions from an async state machine")

        state = self.state
        state_obj = self.sm.get_state(state)

        if not include_waiting and state_obj.is_waiting:
            return []

        triggers = self.sm.get_triggers(state)
        actions = []

        for t in triggers:
            if t not in self.explicit_transitions:
                continue

            can_trigger = self.may_trigger(t)

            if not can_trigger:
                continue

            event = self.sm.events.get(t)
            for source, transitions in event.transitions.items():
                if state.startswith(source):
                    transition = transitions[0]
                    action = self.transition_to_action(t, transition)
                    actions.append(action)

        return actions

    def is_transition_valid(self, transition: ts.Transition):
        """Check if a transition is valid based on current state conditions.

        Args:
            transition (ts.Transition): Transition to check.

        Returns:
            bool: Whether the transition is valid.

        Example:
            >>> machine = SherpaStateMachine(states=["idle", "working"])
            >>> transition = ts.Transition(
            ...     machine.sm, "start", "idle", "working"
            ... )
            >>> print(machine.is_transition_valid(transition))
            True
        """
        return self.sm._transition_for_model(transition)

    def get_current_state(self) -> ts.State:
        """Get the current state of the state machine.

        Returns:
            ts.State: Current state object.

        Example:
            >>> machine = SherpaStateMachine(states=["idle", "working"])
            >>> state = machine.get_current_state()
            >>> print(state.name)
            'idle'
        """
        return self.sm.get_state(self.state)

    def get_state(self, state: str) -> ts.State:
        """
        Get the state object from the state machine

        Args:
            state (str): the name of the state

        Returns:
            ts.State: the state object
        """
        return self.sm.get_state(state)

    def extract_actions_info(
        self, actions: list[BaseAction], args: dict, description: str
    ):
        """Extract information about available actions.

        Args:
            actions (list[BaseAction]): List of actions to extract info from.
            args (dict): Arguments for the actions.
            description (str): Description of the action context.

        Returns:
            dict: Dictionary containing action information.

        Example:
            >>> machine = SherpaStateMachine()
            >>> actions = [BaseAction(name="action1")]
            >>> info = machine.extract_actions_info(actions, {}, "context")
            >>> print(info["actions"])
            [{'name': 'action1', 'description': ''}]
        """
        # late import to avoid circular import issues
        from sherpa_ai.actions.base import ActionArgument, BaseAction

        for action in actions:
            if isinstance(action, str):
                action = getattr(self, action)

            # refresh the usage or argument attributes of the action
            if isinstance(action, BaseAction):
                _ = str(action)

                for arg in action.args:
                    if type(arg) is str:
                        arg_usage = action.args[arg]
                        new_arg = ActionArgument(name=arg, description=arg_usage)
                        arg_name = arg
                    else:
                        new_arg = arg.model_copy()
                        arg_name = new_arg.name

                    if arg_name in args:
                        logger.warning(
                            f"Duplicate argument {arg} in action {action.name}"
                        )
                    args[arg_name] = new_arg

                description += f". Next, {action.usage}"

        return args, description

    def transition_to_action(
        self, trigger: str, transition: ts.Transition
    ) -> BaseAction:
        """Convert a transition to an action.

        Args:
            trigger (str): Trigger event name.
            transition (ts.Transition): Transition to convert.

        Returns:
            BaseAction: Action representing the transition.

        Example:
            >>> machine = SherpaStateMachine(states=["idle", "working"])
            >>> transition = ts.Transition(
            ...     machine.sm, "start", "idle", "working"
            ... )
            >>> action = machine.transition_to_action("start", transition)
            >>> print(action.name)
            'start'
        """
        # late import to avoid circular import issues
        from sherpa_ai.actions.dynamic import AsyncDynamicAction, DynamicAction

        def wrapper_action(**kwargs):
            transit_trigger = getattr(self, trigger)
            result = transit_trigger(**kwargs)

            if not isinstance(result, str):
                return str(result)
            else:
                return result

        async def async_wrapper_action(**kwargs):
            transit_trigger = getattr(self, trigger)
            result = await transit_trigger(**kwargs)

            if not isinstance(result, str):
                return str(result)
            else:
                return result

        usage = transition.description
        args = {}
        source_state = self.get_state(transition.source)
        dest_state = self.get_state(transition.dest)

        # gather callback information from the source and destination states
        args, usage = self.extract_actions_info(source_state.on_exit, args, usage)
        args, usage = self.extract_actions_info(transition.before, args, usage)
        args, usage = self.extract_actions_info(dest_state.on_enter, args, usage)
        args, usage = self.extract_actions_info(transition.after, args, usage)

        # convert arguments back to list
        args = list(args.values())

        name = trigger
        # Append the transition to the usage
        usage += f" Transit the state from {transition.source} to {transition.dest}"

        # Select the wrapper action based on the type of the state machine
        if "async" in self.sm.__class__.__name__.lower():
            action = AsyncDynamicAction(
                name=name, args=args, usage=usage, action=async_wrapper_action
            )
        else:
            action = DynamicAction(
                name=name, args=args, usage=usage, action=wrapper_action
            )

        return action

    def is_async(self):
        """Check if the state machine is asynchronous.

        Returns:
            bool: True if the state machine is async, False otherwise.

        Example:
            >>> machine = SherpaStateMachine()
            >>> print(machine.is_async())
            False
        """
        return "async" in type(self.sm).__name__.lower()
