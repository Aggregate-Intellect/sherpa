from unittest.mock import Mock, patch

import pytest

from sherpa_ai.utils import (
    get_base_url,
    get_links_from_string,
    log_formatter,
    question_reconstructor,
    scrape_with_url,
    show_commands_only,
)


def test_get_links_from_string_succeeds():
    text_with_link = "this is the link for ui/ux <https://ui8.net/artpaperdsgn/products/e-commerce-shopping-and-marketing-3d> , <http://codepen.io/trending> "
    return_data = get_links_from_string(text_with_link)
    assert str(return_data) == "[{'url': 'https://ui8.net/artpaperdsgn/products/e-commerce-shopping-and-marketing-3d', 'base_url': 'https://ui8.net'}, {'url': 'http://codepen.io/trending', 'base_url': 'http://codepen.io'}]"

def test_get_base_url_succeeds():
    data = "https://ui8.net/artpaperdsgn/products/e-commerce-shopping-and-marketing-3d"
    return_data = get_base_url(data)
    assert str(return_data)=="https://ui8.net"

def test_scrape_with_url_handles_valid_html_content():
    mock_get = Mock()
    mock_get.return_value.status_code = 200
    mock_get.return_value.content = b'<html><body>Hello, World!</body></html>'
    with patch('requests.get', mock_get):
        result = scrape_with_url('http://example.com')
    assert result['status'] == 200
    assert result['data'] == 'Hello, World!'

def test_scrape_with_url_handles_url_not_found():
    mock_get = Mock()
    mock_get.return_value.status_code = 404
    mock_get.return_value.content = b'Not Found'
    with patch('requests.get', mock_get):
        result = scrape_with_url('http://example.com')
    assert result['status'] == 404
    assert result['data'] == ''

def test_question_reconstructor_succeeds():
    data = [{'data': ' a comparison of five open-source large language models (LLMs) that are making waves in the AI community. Each model is discussed in detail, including their features, performance metrics, and training data. The models discussed are Llama 2, Claude 2, MPT-7B, Falcon, and Vicuna-13B. These models are designed to provide users with extended and coherent responses, process lengthy inputs, and produce accurate and reliable results. They are also optimized for swift training and inference, and are available for commercial use.  a discussion of the current state of Large Language Models (LLMs) and their potential applications. It covers Vicuna-13B, an open-source model that has been fine-tuned on LLaMA, and Falcon, another open-source model with superior performance metrics. It also discusses the collaborative spirit of the AI community and the potential of open-source models to shape the future of AI.', 'link': 'https://www.unite.ai/best-open-source-llms/'}]
    question = "<@U05HDFV64AU> what is this link talking about <https://www.unite.ai/best-open-source-llms/>"
    expected_result = """<@U05HDFV64AU> what is this link talking about [1]./n Reference: [1] link: "https://www.unite.ai/best-open-source-llms/" , link_data:  a comparison of five open-source large language models (LLMs) that are making waves in the AI community. Each model is discussed in detail, including their features, performance metrics, and training data. The models discussed are Llama 2, Claude 2, MPT-7B, Falcon, and Vicuna-13B. These models are designed to provide users with extended and coherent responses, process lengthy inputs, and produce accurate and reliable results. They are also optimized for swift training and inference, and are available for commercial use.  a discussion of the current state of Large Language Models (LLMs) and their potential applications. It covers Vicuna-13B, an open-source model that has been fine-tuned on LLaMA, and Falcon, another open-source model with superior performance metrics. It also discusses the collaborative spirit of the AI community and the potential of open-source models to shape the future of AI."""
    result = question_reconstructor(data, question)
    assert result == expected_result
    
def test_show_commands_only_succeeds():
    # Test input data
    logs = [
        {
            'Step': '0/5',
            'reply': {
                'thoughts': {
                    'text': 'I received a greeting from the user.',
                    'speak': 'The user greeted me.'
                },
                'command': {
                    'name': 'search',
                    'args': {
                        'query': 'How to test in Python?'
                    }
                }
            }
        },
        {
            'Step': '1/5',
            'reply': {
                'thoughts': {
                    'text': 'Searching for Python testing tutorials.',
                    'speak': 'I am searching for Python testing tutorials.'
                },
                'command': {
                    'name': 'continue',
                    'args': {
                        'query': 'How to test in Python?'
                    }
                }
            }
        },
        {
            'Step': '2/5',
            'reply': {
                'thoughts': {
                    'text': 'Found a helpful tutorial.',
                    'speak': 'I found a helpful tutorial.'
                },
                'command': {
                    'name': 'finish',
                    'args': {
                        'response': 'Here is a Python testing tutorial.'
                    }
                }
            }
        }
    ]

    expected_result = (
        "Step: 0/5 \n🛠️search \n❓query: How to test in Python?\n"
        "Step: 1/5 \n🛠️continue \n❓query: How to test in Python?\n"
        "💡Thought process finished!"
    )

    result = show_commands_only(logs)

    assert result == expected_result

@pytest.fixture
def logs_with_thoughts_and_command():
    return [
        {"Step": 1, "reply": {"thoughts": "Thinking..."}},
        {"Step": 2, "reply": {"thoughts": "Still thinking...", "command": "Do something else"}},
    ]

@pytest.fixture
def logs_with_final_response():
    return [
        {"Step": 1, "reply": "This is the final response."},
        {"Step": 2, "reply": "Another final response."},
    ]

def test_format_logs_with_thoughts_and_command_succeeds(logs_with_thoughts_and_command):
    expected_output = (
        "-- Step: 1 -- \nThoughts: \n Thinking..."
        "\n-- Step: 2 -- \nThoughts: \n Still thinking... \nCommand: \n Do something else"
    )
    assert log_formatter(logs_with_thoughts_and_command) == expected_output

def test_format_logs_with_final_response_succeeds(logs_with_final_response):
    expected_output = (
        "-- Step: 1 -- \nFinal Response: \n This is the final response."
        "\n-- Step: 2 -- \nFinal Response: \n Another final response."
    )
    assert log_formatter(logs_with_final_response) == expected_output