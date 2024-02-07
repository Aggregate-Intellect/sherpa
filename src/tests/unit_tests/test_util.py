from unittest.mock import Mock, patch

import pytest

from sherpa_ai.utils import (
    check_if_number_exist,
    extract_numbers_from_text,
    get_base_url,
    get_links_from_string,
    log_formatter,
    rewrite_link_references,
    scrape_with_url,
    show_commands_only,
)


def test_get_links_from_string_succeeds():
    text_with_link = "this is the link for ui/ux <https://ui8.net/artpaperdsgn/products/e-commerce-shopping-and-marketing-3d> , <http://codepen.io/trending> "
    return_data = get_links_from_string(text_with_link)
    assert (
        str(return_data)
        == "[{'url': 'https://ui8.net/artpaperdsgn/products/e-commerce-shopping-and-marketing-3d', 'base_url': 'https://ui8.net'}, {'url': 'http://codepen.io/trending', 'base_url': 'http://codepen.io'}]"
    )


def test_get_base_url_succeeds():
    data = "https://ui8.net/artpaperdsgn/products/e-commerce-shopping-and-marketing-3d"
    return_data = get_base_url(data)
    assert str(return_data) == "https://ui8.net"


def test_scrape_with_url_handles_valid_html_content():
    mock_get = Mock()
    mock_get.return_value.status_code = 200
    mock_get.return_value.content = b"<html><body>Hello, World!</body></html>"
    with patch("requests.get", mock_get):
        result = scrape_with_url("http://example.com")
    assert result["status"] == 200
    assert result["data"] == "Hello, World!"


def test_scrape_with_url_handles_url_not_found():
    mock_get = Mock()
    mock_get.return_value.status_code = 404
    mock_get.return_value.content = b"Not Found"
    with patch("requests.get", mock_get):
        result = scrape_with_url("http://example.com")
    assert result["status"] == 404
    assert result["data"] == ""


def test_rewrite_link_references_succeeds():
    data = [
        {
            "data": " a comparison of five open-source large language models (LLMs) that are making waves in the AI community. Each model is discussed in detail, including their features, performance metrics, and training data.",
            "link": "https://www.unite.ai/best-open-source-llms/",
        }
    ]
    question = "<@U05HDFV64AU> what is this link talking about <https://www.unite.ai/best-open-source-llms/>"
    expected_result = """<@U05HDFV64AU> what is this link talking about [1]./n Reference: [1] link: "https://www.unite.ai/best-open-source-llms/" , link_data: [{'data': ' a comparison of five open-source large language models (LLMs) that are making waves in the AI community. Each model is discussed in detail, including their features, performance metrics, and training data.', 'link': 'https://www.unite.ai/best-open-source-llms/'}]"""

    result = rewrite_link_references(data, question)
    assert result == expected_result


def test_show_commands_only_succeeds():
    # Test input data
    logs = [
        {
            "Step": "0/5",
            "reply": {
                "thoughts": {
                    "text": "I received a greeting from the user.",
                    "speak": "The user greeted me.",
                },
                "command": {
                    "name": "search",
                    "args": {"query": "How to test in Python?"},
                },
            },
        },
        {
            "Step": "1/5",
            "reply": {
                "thoughts": {
                    "text": "Searching for Python testing tutorials.",
                    "speak": "I am searching for Python testing tutorials.",
                },
                "command": {
                    "name": "continue",
                    "args": {"query": "How to test in Python?"},
                },
            },
        },
        {
            "Step": "2/5",
            "reply": {
                "thoughts": {
                    "text": "Found a helpful tutorial.",
                    "speak": "I found a helpful tutorial.",
                },
                "command": {
                    "name": "finish",
                    "args": {"response": "Here is a Python testing tutorial."},
                },
            },
        },
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
        {
            "Step": 2,
            "reply": {"thoughts": "Still thinking...", "command": "Do something else"},
        },
    ]


@pytest.fixture
def logs_with_final_response():
    return [
        {"Step": 1, "reply": "This is the final response."},
        {"Step": 2, "reply": "Another final response."},
    ]


def test_log_formatter_formats_correctly_1(logs_with_thoughts_and_command):
    expected_output = "-- Step: 1 -- \nThoughts: \n Thinking... \n-- Step: 2 -- \nThoughts: \n Still thinking... \nCommand: \n Do something else"
    assert log_formatter(logs_with_thoughts_and_command) == expected_output


def test_log_formatter_formats_correctly_2(logs_with_final_response):
    expected_output = (
        "-- Step: 1 -- \nFinal Response: \n This is the final response."
        "\n-- Step: 2 -- \nFinal Response: \n Another final response."
    )
    assert log_formatter(logs_with_final_response) == expected_output


@pytest.fixture
def source_data():
    return " Cillum labore et culpa elit irure labore nostrud 12.45 minim cupidatat. Nulla nisi aliquip do duis elit tempor magna. Occaecat sunt nisi aliqua officia fugiat. Dolor ea ad mollit nulla ullamco sit voluptate cillum id laboris et proident anim. Culpa officia incididunt sit qui exercitation magna voluptate Lorem duis eu occaecat. Non occaecat deserunt voluptate cillum aliquip voluptate veniam. Ullamco commodo eiusmod consequat dolor cillum quis Lorem $45,000 labore tempor cupidatat  7 elit quis deserunt.  "


@pytest.fixture
def correct_result_data():
    return "Labore deserunt 12.45 $45,000 ,7 sit velit nulla. Sint ipsum reprehenderit sint cupidatat amet est id anim exercitation fugiat adipisicing elit. Id est dolore minim magna occaecat aute. Est dolore culpa laborum non esse nostrud."


@pytest.fixture
def incorrect_result_data():
    return "Labore deserunt 12.45 $45,000 ,7 ,56 , 65 sit velit nulla. Sint ipsum reprehenderit sint cupidatat amet est id anim exercitation fugiat adipisicing elit. Id est dolore minim magna occaecat aute. Est dolore culpa laborum non esse nostrud."


def test_extract_numbers_from_text(source_data):
    extracted_number = extract_numbers_from_text(source_data)

    # source data has these numbers in it
    numbers_in_source_data = ["12.45", "45000", "7"]
    assert len(numbers_in_source_data) == len(
        extracted_number
    ), "failed to extract a number"
    for number in extracted_number:
        assert number in numbers_in_source_data, (
            number + " is not in numbers_in_source_data"
        )


def test_extract_numbers_from_text_pass(source_data, correct_result_data):
    # test aganist a text with the same numbers within it
    check_result = check_if_number_exist(source_data, correct_result_data)
    assert check_result["number_exists"]


def test_extract_numbers_from_text_fails(source_data, incorrect_result_data):
    # test aganist a text which don't have the same numers as the source
    check_result = check_if_number_exist(incorrect_result_data, source_data)
    assert not check_result["number_exists"]
