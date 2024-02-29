from unittest.mock import Mock, patch

import pytest

from sherpa_ai.utils import (
    check_if_number_exist,
    extract_entities,
    extract_numbers_from_text,
    get_base_url,
    get_links_from_string,
    json_from_text,
    log_formatter,
    rewrite_link_references,
    scrape_with_url,
    show_commands_only,
    verify_numbers_against_source,
    string_comparison_with_jaccard_and_levenshtein,
    text_similarity,
    text_similarity_by_metrics,
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


@pytest.mark.parametrize(
    "source_text,source_numbers",
    [
        (
            "nostrud 12.45 minim cupidatat Lorem $45,000 labore7 elit.",
            ["12.45", "45000", "7"],
        ),
        (
            "123something12minim jammed together $45 abore 7 elit123",
            ["123", "12", "45", "7", "123"],
        ),
        ("42 is a 42 with 42plus42 and 42", ["42", "42", "42", "42", "42"]),
        (
            "No numbers to see here",
            [],
        ),
        (
            None,
            [],
        ),
    ],
)
def test_extract_numbers_from_text(source_text, source_numbers):
    extracted_numbers = extract_numbers_from_text(source_text)
    for number in extracted_numbers:
        assert number in source_numbers, number + " is not in source_numbers"
    assert len(extracted_numbers) == len(
        source_numbers
    ), f"Incorrect extraction from #{ source_text }, expected #{ source_numbers } but got #{ extracted_numbers }"


@pytest.mark.parametrize(
    "text_to_test,source_text",
    [
        (
            "nostrud 12.45 minim cupidatat Lorem $45,000 labore7 elit.",
            "nostrud 12.45 minim cupidatat Lorem $45,000 labore7 elit.",
        ),
        (
            "123something12minim jammed together $45 abore 7 elit123",
            "45 7 123 12 45 7 123",
        ),
        (
            "42 is a 42 with 42plus42 and 42",
            "99999 with a 42 does not add to 991232",
        ),
        (
            "No numbers to see here",
            "99999 with a 42 does not add to 991232",
        ),
        (
            None,
            "This can be anything",
        ),
        (None, None),
    ],
)
def test_verify_numbers_against_source_succeeds(text_to_test, source_text):
    result, msg = verify_numbers_against_source(text_to_test, source_text)
    assert (
        result is True
    ), f"Expected '{ source_text}' to contain all numbers in '{text_to_test}'"
    assert msg is None, f"Expected return message to be None, got { msg } instead"


@pytest.mark.parametrize(
    "text_to_test,source_text",
    [
        (
            "nostrud 12.45 minim cupidatat Lorem $45,000 labore7 elit.",
            "nostrud minim cupidatat Lorem $45,000 labore7 elit.",
        ),
        (
            "123something12minim jammed together $45 abore 7 elit123",
            "45 7 12",
        ),
        (
            "42 is a 42 with 42plus42 and 42",
            "99999 plus 991232",
        ),
        (
            "42",
            None,
        ),
    ],
)
def test_verify_numbers_against_source_fails(text_to_test, source_text):
    result, msg = verify_numbers_against_source(text_to_test, source_text)
    assert (
        result is False
    ), f"Expected '{ source_text}' NOT to contain all numbers in '{text_to_test}'"
    assert (
        "Don't use the numbers" in msg
    ), f"Return message { msg } doesn't contain expected text"
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

def test_json_extractor_valid_json():
    text = "This is some text with {\"key\": \"value\"} JSON data."

    result = json_from_text(text)
    assert result == {"key": "value"}

def test_json_extractor_invalid_json():
    text = "This is some text with invalid JSON data: {\"key\": \"value\",}."
    result = json_from_text(text)
    assert result == {}

def test_json_extractor_no_json():
    text = "This text does not contain any JSON data."
    result = json_from_text(text)
    assert result == {}

def test_json_extractor_empty_string():
    text = ""
    result = json_from_text(text)
    assert result == {}

def test_json_extractor_nested_json():
    text = "Nested JSON: {\"key1\": {\"key2\": \"value\"}}"
    result = json_from_text(text)
    assert result == {"key1": {"key2": "value"}}




def test_extract_entities_with_entities():
    text = "The United Nations (ORG) is an international organization. Some countries are members of NORP, while others are not."
    result = extract_entities(text)
    assert result == ["The United Nations", "NORP"]

def test_extract_entities_without_entities():
    text = "This text does not contain any relevant entities."
    result = extract_entities(text)
    assert result == []

def test_extract_entities_empty_string():
    text = ""
    result = extract_entities(text)
    assert result == []

def test_string_comparison_function():
    assert string_comparison_with_jaccard_and_levenshtein("hello", "hello", 0.5) == 1.0
    assert string_comparison_with_jaccard_and_levenshtein("hello", "world", 0.5) <= 0.3 
    assert string_comparison_with_jaccard_and_levenshtein("openai", "open", 0.5) > 0.7
    assert string_comparison_with_jaccard_and_levenshtein("car", "bat", 0.5) == 0.0

def test_text_similarity_entities_present():
    check_entity = ["apple", "banana", "orange"]
    source_entity = ["apple", "orange"]
    result = text_similarity(check_entity, source_entity)
    assert result["entity_exist"] == True
    assert result["messages"] == ""

def test_text_similarity_entities_not_present():
    check_entity = ["apple", "banana", "orange"]
    source_entity = ["grape", "kiwi", "pear"]
    result = text_similarity(check_entity, source_entity)
    assert result["entity_exist"] == False
    expected_message = "remember to address these entities grape, kiwi, pear,  in final the answer."
    assert result["messages"] == expected_message


def test_text_similarity_with_entities_exist():
    check_entity = ["apple", "banana", "orange"]
    source_entity = ["apple", "orange"]
    result = text_similarity_by_metrics(check_entity, source_entity)
    assert result["entity_exist"] is True
    assert result["messages"] == ""


def test_text_similarity_with_entities_exist():
    check_entity = ["apple", "banana", "orange"]
    source_entity = ["apples", "oranges"]
    result = text_similarity_by_metrics(check_entity, source_entity)
    assert result["entity_exist"] is True
    assert result["messages"] == ""


def test_text_similarity_with_entities_not_exist():
    check_entity = ["apple", "orange", "banana"]
    source_entity = ["pear", "grape", "kiwi"]
    result = text_similarity_by_metrics(check_entity, source_entity)
    assert result["entity_exist"] is False
    expected_message = "remember to address these entities pear, grape, kiwi,  in final the answer."
    assert result["messages"] == expected_message
