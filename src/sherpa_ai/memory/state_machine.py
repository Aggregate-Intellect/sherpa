from typing import Callable, Optional, Union

from loguru import logger
from transitions import Machine, Transition

from sherpa_ai.actions.base import BaseAction
from sherpa_ai.actions.dymatic import DynamicAction
from sherpa_ai.actions.empty import EmptyAction


class SherpaStateMachine(Machine):
    explicit_transitions: set = set()

    def __init__(self, auto_transitions: bool = False, **kwargs):
        # By default, do not create dummy fully connected transitions
        super().__init__(auto_transitions=auto_transitions, **kwargs)

    def add_transition(
        self,
        name: str,
        source: Union[str, list[str]],
        dest: Union[str, list[str]],
        conditions: Union[Callable, list[Callable]] = None,
        unless: Union[Callable, list[Callable]] = None,
        action: Optional[BaseAction] = None,
    ):
        self.explicit_transitions.add(name)
        logger.error(name)

        if not action:
            action = EmptyAction(usage="")

        super().add_transition(
            trigger=name,
            source=source,
            dest=dest,
            conditions=conditions,
            unless=unless,
            prepare=action,
        )

    def get_actions(self) -> list[BaseAction]:
        state = self.model.state
        triggers = self.get_triggers(state)
        actions = []

        logger.error(triggers)

        for t in triggers:
            if t not in self.explicit_transitions:
                continue

            transition = self.get_transitions(t, source=state)[0]

            action = self.transition_to_action(t, transition)
            actions.append(action)

        return actions

    def transition_to_action(self, trigger: str, transition: Transition) -> BaseAction:
        """
        Wrap a transition into a BaseAction that can be selected by an agent
        """

        def wrapper_action(**kwargs):
            transit_trigger = getattr(self.model, trigger)
            transit_trigger()

        usage = transition.prepare[0].usage
        args = transition.prepare[0].args
        name = trigger

        # Append the transition to the usage
        usage += f" Transit the state from {transition.source} to {transition.dest}"

        action = DynamicAction(name=name, args=args, usage=usage, action=wrapper_action)

        return action
