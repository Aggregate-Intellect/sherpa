import copy
import sys
from typing import Callable

import pytest
from loguru import logger


def get_new_logger(filename, level="INFO") -> Callable[[str], type(logger)]:
    """
    Get a new logger that logs to a file while keeping the global logger unchanged.
    Reference: https://github.com/Delgan/loguru/issues/487
    """
    logger.remove()
    child_logger = copy.deepcopy(logger)

    # add handler back
    logger.add(sys.stderr)

    child_logger.add(filename, level=level, format="{message}", mode="w")

    return child_logger


@pytest.fixture
def config_logger_level() -> Callable[[str], None]:
    def get(level="DEBUG"):
        logger.remove()
        logger.add(sys.stderr, level=level)

    return get
