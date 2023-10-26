
from sherpa_ai.status_loggers.base import BaseStatusLogger
from typing import Callable, List

class SlackStatusLogger(BaseStatusLogger):
    """
    A logger that sends messages to Slack
    """

    # the say utility function from Bolt
    logger: Callable[[str], None]
    thread_ts: str

    def __init__(self, logger: Callable[[str], None], thread_ts: str):
        self.logger = logger
        self.thread_ts = thread_ts

    def log(self, message: str):
        self.logger(message, thread_ts=self.thread_ts)


class DummyStatusLogger(BaseStatusLogger):
    """
    A logger that does nothing when the status logger is on is not on
    """

    def log(self, message: str):
        pass

