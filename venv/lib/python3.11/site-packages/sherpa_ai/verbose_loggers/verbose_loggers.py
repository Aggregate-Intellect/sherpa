from typing import Callable, List

from sherpa_ai.verbose_loggers.base import BaseVerboseLogger


class SlackVerboseLogger(BaseVerboseLogger):
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


class DummyVerboseLogger(BaseVerboseLogger):
    """
    A logger that does nothing when the verbose is not on
    """

    def log(self, message: str):
        pass


class StorageVerboseLogger(BaseVerboseLogger):
    """
    A logger that stores all messages in a list, for testing purpose
    """

    storage: List[str]

    def __init__(self):
        self.storage = []

    def log(self, message: str):
        self.storage.append(message)
