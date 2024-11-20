import inspect

from transitions import State, Transition

"""
Additional features for states and transitions in the state machine.

See https://github.com/pytransitions/transitions?tab=readme-ov-file#adding-features-to-states for more details
"""  # noqa: E501


class StateDesc(State):
    """
    Allows states to have a description, including how it should be transited into
    other states.

    Attributes:
        description (str): description of the state
    """

    def __init__(self, *args, **kwargs):
        """
        Args:
            **kwargs: If kwargs contains `description`, assign it to the attribute.
        """
        self.description = kwargs.pop("description", "")
        super(StateDesc, self).__init__(*args, **kwargs)


class TransitionDesc(Transition):
    """
    Allows transitions to have a description.

    Attributes:
        description (str): description of the transition
    """

    def __init__(self, *args, **kwargs):
        """
        Args:
            **kwargs: If kwargs contains `description`, assign it to the attribute.
        """
        self.description = kwargs.pop("description", "")
        super(TransitionDesc, self).__init__(*args, **kwargs)


def add_transition_features(*args):
    """
    Transition class feature decorator. Adds the features to the transition class.
    """

    def _class_decorator(cls):
        class CustomTransition(type("CustomTransition", args, {}), cls.transition_cls):
            """
            The decorated Transition. Inherits from the Transition class used by the decorated Machine.
            """  # noqa: E501

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
