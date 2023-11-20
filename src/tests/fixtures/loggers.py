import copy
import sys
from typing import Callable

import pytest
from loguru import logger


@pytest.fixture
def get_logger() -> Callable[[str], type(logger)]:
    def get(filename):
        logger.remove()
        child_logger = copy.deepcopy(logger)

        # add handler back
        logger.add(sys.stderr)

        child_logger.add(filename, level="INFO", format="{message}")

        return child_logger

    return get
