import base64
from unittest import mock

import pytest

from sherpa_ai.scrape.extract_github_readme import extract_github_readme


def mock_request(url, **kwargs):
    response = mock.Mock()
    if ".md" in url:
        # return mock readme
        response.json = mock.Mock(
            return_value={"content": base64.b64encode("mock readme".encode())}
        )
    else:
        response.json = mock.Mock(return_value=[{"name": "readme.md"}])

    return response


@pytest.fixture
def mock_requests(external_api: bool):
    if external_api:
        yield
        return

    with mock.patch("requests.get") as mock_get, mock.patch(
        "sherpa_ai.scrape.extract_github_readme.save_to_pine_cone"
    ):
        mock_get.side_effect = mock_request
        yield


def test_extract_github_readme_with_valid_url_succeeds(
    mock_requests,
):
    repo_url = "https://github.com/Aggregate-Intellect/sherpa"
    content = extract_github_readme(repo_url)

    assert content is None or len(content) > 0


def test_extract_github_readme_with_invalid_url_succeeds(mock_requests):
    repo_url = "https://google.com"
    content = extract_github_readme(repo_url)

    assert content is None
