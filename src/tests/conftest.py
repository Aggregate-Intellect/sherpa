import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--external_api",
        action="store_true",
        default=False,
        help="run the test with actual external API calls",
    )


@pytest.fixture
def external_api(request):
    return request.config.getoption("--external_api")
