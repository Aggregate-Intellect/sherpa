"""State machine utility module for Sherpa AI.

This module provides utility classes and functions for extending the functionality
of the state machine implementation. It includes classes for adding descriptions
to states and transitions, and a decorator for adding features to transition classes.

See https://github.com/pytransitions/transitions?tab=readme-ov-file#adding-features-to-states for more details
"""

import inspect

from transitions import State, Transition


class StateDesc(State):
    """Extended state class with description support.

    This class extends the base State class to add description functionality,
    allowing states to have a description of their purpose and transition behavior.

    Attributes:
        description (str): Description of the state and its transitions.

    Example:
        >>> state = StateDesc("working", description="State for processing tasks")
        >>> print(state.description)
        'State for processing tasks'
    """

    def __init__(self, *args, **kwargs):
        """Initialize a state with description.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments. If 'description' is present,
                     it will be assigned to the state's description attribute.

        Example:
            >>> state = StateDesc("idle", description="Initial state")
            >>> print(state.description)
            'Initial state'
        """
        self.description = kwargs.pop("description", "")
        super(StateDesc, self).__init__(*args, **kwargs)


class TransitionDesc(Transition):
    """Extended transition class with description support.

    This class extends the base Transition class to add description functionality,
    allowing transitions to have a description of their purpose and behavior.

    Attributes:
        description (str): Description of the transition.

    Example:
        >>> transition = TransitionDesc("start", description="Start processing")
        >>> print(transition.description)
        'Start processing'
    """

    def __init__(self, *args, **kwargs):
        """Initialize a transition with description.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments. If 'description' is present,
                     it will be assigned to the transition's description attribute.

        Example:
            >>> transition = TransitionDesc("stop", description="Stop processing")
            >>> print(transition.description)
            'Stop processing'
        """
        self.description = kwargs.pop("description", "")
        super(TransitionDesc, self).__init__(*args, **kwargs)


def add_transition_features(*args):
    """Decorator for adding features to transition classes.

    This function creates a decorator that adds the specified features to a
    transition class. It combines the features with the existing transition
    class to create a new class with enhanced functionality.

    Args:
        *args: Feature classes to add to the transition class.

    Returns:
        Callable: Decorator function that adds the features to the target class.

    Example:
        >>> @add_transition_features(Feature1, Feature2)
        ... class MyMachine(Machine):
        ...     pass
        >>> print(hasattr(MyMachine.transition_cls, 'feature1'))
        True
    """
    def _class_decorator(cls):
        class CustomTransition(type("CustomTransition", args, {}), cls.transition_cls):
            """Custom transition class with added features.

            This class combines the features specified in the decorator with
            the base transition class to create an enhanced transition class.

            Attributes:
                dynamic_methods (list): List of dynamic methods available to the transition.
            """

        method_list = sum(
            [
                c.dynamic_methods
                for c in inspect.getmro(CustomTransition)
                if hasattr(c, "dynamic_methods")
            ],
            [],
        )
        CustomTransition.dynamic_methods = list(set(method_list))
        cls.transition_cls = CustomTransition
        return cls

    return _class_decorator
