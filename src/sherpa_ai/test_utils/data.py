"""Test data utilities for Sherpa AI.

This module provides utilities for managing test data files and paths.
It includes functions for locating and accessing test data files relative
to test file locations.
"""

import re

import pytest


@pytest.fixture
def get_test_data_file_path():
    """Pytest fixture for getting test data file paths.

    This fixture provides a function that constructs paths to test data files
    relative to the location of the test file using them.

    Returns:
        Callable[[str, str, str], str]: Function to get test data file paths.

    Example:
        >>> def test_data(get_test_data_file_path):
        ...     path = get_test_data_file_path(
        ...         __file__,
        ...         "sample.json",
        ...         folder="test_data"
        ...     )
        ...     with open(path) as f:
        ...         data = json.load(f)
    """
    def get(test_filename: str, file_to_load: str, folder: str = "data") -> str:
        """Get the path to a test data file.

        Args:
            test_filename (str): Path to the test file.
            file_to_load (str): Name of the data file to load.
            folder (str): Name of the folder containing test data.

        Returns:
            str: Full path to the test data file.
        """
        path = re.split("(\\\\|/)tests", test_filename)[0]
        folder = f"{path}/tests/{folder}"
        return f"{folder}/{file_to_load}"

    return get
