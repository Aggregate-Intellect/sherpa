from typing import Any, Callable, Optional, Union

import transitions as ts
from loguru import logger
from pydantic import BaseModel
from transitions.extensions import HierarchicalMachine

from sherpa_ai.actions.base import BaseAction
from sherpa_ai.actions.dynamic import DynamicAction
from sherpa_ai.actions.empty import EmptyAction


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

        for name, action in action_map.items():
            self.__setattr__(name, action)

            # sm_cls.state_cls = State
            # sm_cls.transition_cls = Transition

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
        unless: Union[Callable, list[Callable]] = None,
        action: Optional[BaseAction] = None,
    ):
        self.explicit_transitions.add(trigger)

        if not action:
            action = EmptyAction(usage="")

        if len(self.sm.get_transitions(trigger, source, dest)) > 0:
            self.sm.remove_transition(trigger, source, dest)

        self.sm.add_transition(
            trigger=trigger,
            source=source,
            dest=dest,
            conditions=conditions,
            unless=unless,
            prepare=action,
        )

    def get_actions(self) -> list[BaseAction]:
        state = self.state
        triggers = self.sm.get_triggers(state)
        actions = []

        for t in triggers:
            if t not in self.explicit_transitions:
                continue

            event = self.sm.events.get(t)
            for source, transitions in event.transitions.items():
                if state.startswith(source):
                    transition = transitions[0]
                    action = self.transition_to_action(t, transition)
                    actions.append(action)

        return actions

    def transition_to_action(
        self, trigger: str, transition: ts.Transition
    ) -> BaseAction:
        """
        Wrap a transition into a BaseAction that can be selected by an agent
        """

        def wrapper_action(**kwargs):
            transit_trigger = getattr(self, trigger)
            result = transit_trigger(**kwargs)

            if not isinstance(result, str):
                return str(result)
            else:
                return result

        if len(transition.before) > 0:
            action = transition.before[0]
            if isinstance(action, str):
                action = getattr(self, action)

            # refresh the usage or argument attributes of the action
            _ = str(action)

            usage = action.usage
            args = action.args
            action.name = trigger
        else:
            usage = trigger
            args = {}
        name = trigger

        # Append the transition to the usage
        usage += f" Transit the state from {transition.source} to {transition.dest}"

        action = DynamicAction(name=name, args=args, usage=usage, action=wrapper_action)

        return action
