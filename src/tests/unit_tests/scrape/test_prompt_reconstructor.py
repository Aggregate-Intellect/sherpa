from unittest.mock import patch

import pytest

from sherpa_ai.scrape.prompt_reconstructor import PromptReconstructor

# Assuming that 'your_module' contains the 'PromptReconstructor' class

@pytest.fixture
def mock_get_link_from_slack_client_conversation():
    return [   {"url": "https://google.com", "base_url":"https://google.com"}]  # Replace with the desired mocked result

@pytest.fixture
def mock_scrape_with_url():
    return {"data": "this is the data", "status": 200}  # Replace with the desired mocked result

@pytest.fixture
def mock_chunk_and_summarize():
    return "data"
    # return string  # Replace with the desired mocked result


def test_reconstruct_prompt_with_link_inside_succeeds(
    mock_get_link_from_slack_client_conversation, mock_scrape_with_url,mock_chunk_and_summarize
):
    question = "Here's a <https://google.com>"
    slack_message = ""

    reconstructor = PromptReconstructor(question, slack_message)
    with patch(
        "sherpa_ai.scrape.prompt_reconstructor.chunk_and_summarize",
        return_value=mock_chunk_and_summarize,
    ), patch(
        "sherpa_ai.scrape.prompt_reconstructor.get_link_from_slack_client_conversation",
        return_value=mock_get_link_from_slack_client_conversation,
    ), patch(
        "sherpa_ai.utils.chunk_and_summarize",
        return_value=mock_get_link_from_slack_client_conversation,
    ), patch(
        "sherpa_ai.utils.scrape_with_url",
        return_value=mock_scrape_with_url,
    ):
        reconstructed_prompt = reconstructor.reconstruct_prompt()

    assert reconstructed_prompt == f"""Here's a [1]./n Reference: [1] link: "https://google.com" , link_data: [{{'data': '{mock_chunk_and_summarize}', 'link': 'https://google.com'}}]"""

# def test_reconstruct_prompt_with_out_link():

# def test_reconstruct_prompt_with_github_link():