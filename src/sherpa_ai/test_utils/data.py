import re

import pytest


@pytest.fixture
def get_test_data_file_path():
    def get(test_filename: str, file_to_load: str, folder: str = "data") -> str:
        path = re.split("(\\\\|/)tests", test_filename)[0]
        folder = f"{path}/tests/{folder}"
        return f"{folder}/{file_to_load}"

    return get
