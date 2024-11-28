import asyncio
from typing import Any, Callable, Optional, Union

import transitions as ts
from loguru import logger
from transitions.extensions.states import Tags, add_state_features

from sherpa_ai.actions.base import BaseAction
from sherpa_ai.actions.dynamic import AsyncDynamicAction, DynamicAction
from sherpa_ai.memory.utils import StateDesc, TransitionDesc, add_transition_features


class State(ts.State):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Transition(ts.Transition):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class SherpaStateMachine:
    """
    State machine for defining the behavior of an agent in sherpa

    It combines with a set of states and transitions between them
    Attributes:
        explicit_transitions: set of triggers that are explicitly defined in the
            transitions
        sm: the state machine object from pytransitions
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
        """
        Initialize the state machine

        Args:
            name (str): name of the state machine
            states (list): list of states in the state machine
            transitions (list): list of transitions connecting all states
            initial (str): the name of initial state
            auto_transitions (bool): whether to allow automatically building
                transitions from each pair of states
            sm_cls (type): the state machine class to instantiate the state machine
            action_map (dict): mapping from action name to action object
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
        """
        Add explicit transitions to the state machine

        Args:
            transitions (list): list of explicit transitions to add
        """

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
        """
        Update or add a transition to the state machine

        Args:
            trigger (str): the trigger event for the transition
            source (str): the name of the source state of the transition
            dest (str): the name of the destination state of the transition
            conditions (list): list of conditions checking functions that needs to
                return True before the transition can happen
            action (BaseAction): the action to be executed before the transition happens
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

    def get_actions(self, include_waiting: bool = False) -> list[BaseAction]:
        """
        Get the available transitions as list of actions based on the current state

        Args:
            include_waiting (bool): whether to include transitions from the waiting states

        Returns:
            list[BaseAction]: list of actions that can be executed from the current
                state
        """  # noqa: E501
        state = self.state
        state_obj = self.sm.get_state(state)

        if not include_waiting and state_obj.is_waiting:
            return []

        triggers = self.sm.get_triggers(state)
        actions = []

        for t in triggers:
            if t not in self.explicit_transitions:
                continue

            if self.is_async():
                can_trigger = asyncio.run(self.may_trigger(t))
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

    def is_transition_valid(self, transition: ts.Transition):
        """
        Check if a transition is valid based on the current state by checking it's
            conditions

        Args:
            transition (ts.Transition): the transition object to be checked

        Returns:
            bool: whether the transition is valid
        """
        return self.sm._transition_for_model(transition)

    def get_current_state(self) -> ts.State:
        """
        Get the current state of the state machine

        Returns:
            ts.State: the current state object
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
        """
        Extract the information from a list of actions

        Args:
            actions (list[BaseAction]): the list of actions to extract information from
            args (dict): the argument dictionary to put the action arguments to
            description (str): the description to concatenate action descriptions to

        Returns:
            Tuple(dict, str): the updated argument dictionary and the concatenated
        """
        for action in actions:
            if isinstance(action, str):
                action = getattr(self, action)

            # refresh the usage or argument attributes of the action
            if isinstance(action, BaseAction):
                _ = str(action)

                for arg in action.args:
                    if type(arg) is str:
                        arg_usage = action.args[arg]
                    else:
                        arg_usage = arg.description
                        arg = arg.name

                    if arg in args:
                        logger.warning(
                            f"Duplicate argument {arg} in action {action.name}"
                        )
                    args[arg] = arg_usage

                description += f". Next, {action.usage}"

        return args, description

    def transition_to_action(
        self, trigger: str, transition: ts.Transition
    ) -> BaseAction:
        """
        Wrap a transition into a BaseAction that can be selected by an agent

        Args:
            trigger (str): the trigger event for the transition
            transition (ts.Transition): the transition object to be wrapped

        Returns:
            BaseAction: the action object that can be executed by the agent
        """

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
        return "async" in type(self.sm).__name__.lower()
