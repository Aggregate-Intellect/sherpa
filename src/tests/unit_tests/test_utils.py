from unittest.mock import Mock, patch

import pytest
import requests
from langchain_core.language_models import FakeListLLM
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from sherpa_ai.utils import (
    UnsafeURLError,
    assert_safe_url,
    check_if_number_exist,
    check_url,
    chunk_and_summarize,
    chunk_and_summarize_file,
    combined_number_extractor,
    extract_entities,
    extract_numbers_from_text,
    extract_word_numbers,
    get_base_url,
    get_links_from_string,
    json_from_text,
    log_formatter,
    rewrite_link_references,
    scrape_with_url,
    show_commands_only,
    string_comparison_with_jaccard_and_levenshtein,
    text_similarity,
    text_similarity_by_metrics,
    verify_numbers_against_source,
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
    with patch("socket.getaddrinfo", return_value=[(None, None, None, "", ("93.184.216.34", 0))]), \
         patch("requests.get", mock_get):
        result = scrape_with_url("http://example.com")
    assert result["status"] == 200
    assert result["data"] == "Hello, World!"


def test_scrape_with_url_handles_url_not_found():
    mock_get = Mock()
    mock_get.return_value.status_code = 404
    mock_get.return_value.content = b"Not Found"
    with patch("socket.getaddrinfo", return_value=[(None, None, None, "", ("93.184.216.34", 0))]), \
         patch("requests.get", mock_get):
        result = scrape_with_url("http://example.com")
    assert result["status"] == 404
    assert result["data"] == ""


def test_scrape_with_url_refuses_private_address():
    # SSRF guard: scrape_with_url must reject hosts resolving to internal
    # addresses before ever calling requests.get.
    mock_get = Mock()
    with patch("socket.getaddrinfo", return_value=[(None, None, None, "", ("127.0.0.1", 0))]), \
         patch("requests.get", mock_get):
        with pytest.raises(UnsafeURLError):
            scrape_with_url("http://internal.example")
    mock_get.assert_not_called()


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
    "text,expected",
    [
        ("one thousand two hundred thirty-four", ["1234"]),
        ("twenty one apples", ["21"]),
        ("two point five kilometers", ["2.5"]),
        ("There are one hundred reasons", ["100"]),
    ],
)
def test_extract_word_numbers_finds_real_numbers(text, expected):
    assert extract_word_numbers(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        # "one" and "point" are common non-numeric English words and must
        # not be treated as numbers when they appear alone.
        "That is a fair point, but we need 42 units.",
        "The point of the analysis is clarity.",
        "At one point the shipment was delayed.",
        "No one knows the exact figure.",
        # A repeated word reads as a spoken digit sequence (e.g. a phone
        # number), not an additive/compound number.
        "Phone one one one for support.",
    ],
)
def test_extract_word_numbers_rejects_ambiguous_words(text):
    assert extract_word_numbers(text) == []


@pytest.mark.parametrize(
    "text,expected",
    [
        # Commas separate distinct enumerated numbers rather than joining
        # them into one compound number.
        ("We tried one, two, three approaches.", ["2", "3"]),
        ("Options: five, six or seven days.", ["5", "6", "7"]),
        # A comma inside a compound number splits it into two numbers
        # instead of merging them (documented tradeoff).
        ("one thousand, two hundred thirty-four", ["1000", "234"]),
    ],
)
def test_extract_word_numbers_splits_on_comma(text, expected):
    assert extract_word_numbers(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        # word2number parses a decimal followed by a magnitude as just its
        # integer part, dropping both the fraction and the magnitude.
        ("It cost two point five million dollars.", ["2500000"]),
        ("A one point five million dollar grant.", ["1500000"]),
        ("three point two billion years", ["3200000000"]),
        # A decimal with no magnitude after it is left to word2number.
        ("two point five kilometers", ["2.5"]),
    ],
)
def test_extract_word_numbers_handles_decimal_with_magnitude(text, expected):
    assert extract_word_numbers(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        # "point" at the start or end of a run is the ordinary English noun,
        # not a decimal separator. Dropping it must not take the real numbers
        # beside it along with it.
        ("At some point one hundred people left.", ["100"]),
        ("At this point three items remain.", ["3"]),
        ("To the point five people objected.", ["5"]),
        # ...while a bare "point" with no number beside it still yields nothing.
        ("That is a fair point, but it matters.", []),
    ],
)
def test_extract_word_numbers_keeps_number_beside_nonnumeric_point(text, expected):
    assert extract_word_numbers(text) == expected


def test_verify_numbers_against_source_message_names_the_numbers():
    """The rejection message is fed back to the LLM, so it must name the numbers."""
    ok, message = verify_numbers_against_source(
        "The total was 99 units.", "The total was 42 units."
    )
    assert not ok
    assert "99" in message
    assert "stick to the numbers" in message


def test_check_if_number_exist_message_names_the_numbers():
    result = check_if_number_exist("The total was 99 units.", "The total was 42 units.")
    assert not result["number_exists"]
    assert "99" in result["messages"]
    assert "stick to the numbers" in result["messages"]


def test_combined_number_extractor_matches_digits_and_words():
    result = combined_number_extractor(
        "There were 42 attendees, or about forty-two people."
    )
    assert set(result) == {"42"}


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
    "text_to_test,expected_data",
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
        (None, []),
    ],
)
def test_extract_numbers_from_text_2(text_to_test, expected_data):
    extracted_number = extract_numbers_from_text(text_to_test)
    # source data has these numbers in it
    numbers_in_source_data = expected_data
    assert len(numbers_in_source_data) == len(
        extracted_number
    ), "failed to extract a number"
    for number in extracted_number:
        assert number in numbers_in_source_data, (
            number + " is not in numbers_in_source_data"
        )


@pytest.mark.parametrize(
    "text_to_test, source_text",
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


@pytest.mark.parametrize(
    "text_to_test, source_text, expected_result",
    [
        (
            "nostrud minim cupidatat Lorem $45,000 labore7 elit.",
            "nostrud 12.45 minim cupidatat Lorem $45,000 labore7 elit.",
            True,
        ),
        ("123something12minim jammed together $45 above 7 elit123", "45 7 12", False),
    ],
)
def test_extract_numbers_from_text_3(text_to_test, source_text, expected_result):
    # test against a text which don't have the same numbers as the source
    check_result = check_if_number_exist(text_to_test, source_text)

    assert check_result["number_exists"] == expected_result


def test_json_extractor_valid_json():
    text = 'This is some text with {"key": "value"} JSON data.'
    result = json_from_text(text)
    assert result == {"key": "value"}


@pytest.mark.parametrize(
    "invalid_text",
    [
        'This is some text with invalid JSON data: {"key": "value",}.',
        None,
        "",
        "hi there!",
    ],
)
def test_json_extractor_invalid_json(invalid_text):
    result = json_from_text(invalid_text)
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
    text = 'Nested JSON: {"key1": {"key2": "value"}}'
    result = json_from_text(text)
    assert result == {"key1": {"key2": "value"}}


def test_extract_entities_with_entities():
    text = "The United Nations is an international organization. Some countries are members of the UN, while others are not."
    result = extract_entities(text)
    assert result == ["The United Nations", "UN"]


def test_extract_entities_without_entities():
    text = "This text does not contain any relevant entities."
    result = extract_entities(text)
    assert result == []


def test_extract_entities_empty_string():
    text = ""
    result = extract_entities(text)
    assert result == []


def test_string_comparison_function():
    result1 = string_comparison_with_jaccard_and_levenshtein("hello", "hello", 0.5)
    assert result1 == 1.0

    result2 = string_comparison_with_jaccard_and_levenshtein("hello", "world", 0.5)
    assert result2 <= 0.3

    result3 = string_comparison_with_jaccard_and_levenshtein(
        "openai is a", "open is a", 0.5
    )
    assert result3 > 0.6

    result4 = string_comparison_with_jaccard_and_levenshtein("dog", "bat", 0.5)
    assert result4 == 0.0


def test_text_similarity_entities_present():
    check_entity = ["apple", "banana", "orange"]
    source_entity = ["apple", "orange"]
    entity_exist, message = text_similarity(check_entity, source_entity)
    assert entity_exist is True
    assert message == ""


def test_text_similarity_entities_not_present():
    check_entity = ["apple", "banana", "orange"]
    source_entity = ["grape", "kiwi", "pear"]
    entity_exist, message = text_similarity(check_entity, source_entity)
    assert entity_exist is False
    expected_message = (
        "remember to address these entities grape, kiwi, pear,  in final the answer."
    )
    assert message == expected_message


def test_text_similarity_with_entities_exist():
    check_entity = ["apple", "banana", "orange"]
    source_entity = ["apple", "orange"]
    entity_exist, message = text_similarity_by_metrics(check_entity, source_entity)
    assert entity_exist is True
    assert message == ""


def test_text_similarity_with_entities_not_exist():
    check_entity = ["apple", "orange", "banana"]
    source_entity = ["pear", "grape", "kiwi"]
    entity_exist, message = text_similarity_by_metrics(check_entity, source_entity)

    assert entity_exist is False
    expected_message = (
        "remember to address these entities pear, grape, kiwi,  in the final answer."
    )
    assert message.lower() == expected_message.lower()


@pytest.mark.parametrize(
    "bad_uri",
    [
        "file://something",
        "s3://some-file",
        "javascript:some-code",
        "garbage",
        "FILE://something",
    ],
)
def test_check_url_raises_exception_for_unsupported_uri_scheme(bad_uri):
    with pytest.raises(ValueError):
        check_url(bad_uri)


@pytest.mark.parametrize(
    "good_uri",
    ["http://something.com", "https://something.com"],
)
def test_check_url_returns_true_for_valid_http_url(good_uri):
    mock_response = Mock()
    mock_response.status_code = 200
    with patch("socket.getaddrinfo", return_value=[(None, None, None, "", ("93.184.216.34", 0))]), \
         patch("requests.get", return_value=mock_response):
        result = check_url(good_uri)
    assert result is True


def test_check_url_returns_false_on_request_error():
    with patch("socket.getaddrinfo", return_value=[(None, None, None, "", ("93.184.216.34", 0))]), \
         patch("requests.get", side_effect=Exception("problem")):
        result = check_url("https://anything")
    assert result is False


def test_check_url_returns_false_for_private_address():
    # SSRF guard: a hostname resolving to a private/internal address must
    # not be fetched, even though scheme and DNS resolution succeed.
    with patch("socket.getaddrinfo", return_value=[(None, None, None, "", ("127.0.0.1", 0))]):
        result = check_url("http://internal.example")
    assert result is False


@pytest.mark.parametrize(
    "unsafe_ip",
    [
        "127.0.0.1",  # loopback
        "10.0.0.5",  # private
        "169.254.169.254",  # link-local / cloud metadata endpoint
        "::1",  # loopback (IPv6)
        "100.64.0.5",  # CGNAT space (100.64.0.0/10) - missed by naive denylist
        "::ffff:127.0.0.1",  # IPv4-mapped IPv6 loopback
    ],
)
def test_assert_safe_url_rejects_internal_addresses(unsafe_ip):
    with patch("socket.getaddrinfo", return_value=[(None, None, None, "", (unsafe_ip, 0))]):
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://attacker-controlled.example")


def test_assert_safe_url_accepts_public_address():
    with patch("socket.getaddrinfo", return_value=[(None, None, None, "", ("93.184.216.34", 0))]):
        assert_safe_url("http://something.com")  # should not raise


def test_assert_safe_url_rejects_non_http_scheme():
    with pytest.raises(UnsafeURLError):
        assert_safe_url("file:///etc/passwd")


def test_assert_safe_url_rejects_unresolvable_host():
    import socket as socket_module

    with patch(
        "socket.getaddrinfo",
        side_effect=socket_module.gaierror("name resolution failed"),
    ):
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://does-not-resolve.invalid")


def _redirect_response(location, status_code=302):
    resp = Mock()
    resp.status_code = status_code
    resp.headers = {"Location": location}
    return resp


def test_safe_get_validates_redirect_target_before_following():
    # A public host that 302-redirects to the cloud metadata endpoint must be
    # rejected: the redirect target is validated *before* being followed.
    from sherpa_ai.utils import safe_get

    def fake_getaddrinfo(host, *args, **kwargs):
        mapping = {
            "public.example": "93.184.216.34",
            "169.254.169.254": "169.254.169.254",
        }
        ip = mapping.get(host, "169.254.169.254")
        return [(None, None, None, "", (ip, 0))]

    redirect = _redirect_response("http://169.254.169.254/latest/meta-data/")

    with patch("socket.getaddrinfo", side_effect=fake_getaddrinfo), \
         patch("requests.get", return_value=redirect) as mock_get:
        with pytest.raises(UnsafeURLError):
            safe_get("http://public.example")

    # The first hop was fetched, but the internal redirect target never was.
    assert mock_get.call_count == 1
    for call in mock_get.call_args_list:
        assert "169.254.169.254" not in call.args[0]


def test_safe_get_follows_safe_redirect():
    from sherpa_ai.utils import safe_get

    final = Mock()
    final.status_code = 200
    final.content = b"ok"
    responses = [_redirect_response("http://target.example/final"), final]

    with patch("socket.getaddrinfo", return_value=[(None, None, None, "", ("93.184.216.34", 0))]), \
         patch("requests.get", side_effect=responses) as mock_get:
        result = safe_get("http://start.example")

    assert result is final
    assert mock_get.call_count == 2


def test_safe_get_pins_validated_ip_for_http():
    # For http the request must connect to the validated IP, not the hostname,
    # with the original Host header preserved (defeats DNS rebinding).
    from sherpa_ai.utils import safe_get

    final = Mock()
    final.status_code = 200
    with patch("socket.getaddrinfo", return_value=[(None, None, None, "", ("93.184.216.34", 0))]), \
         patch("requests.get", return_value=final) as mock_get:
        safe_get("http://example.com/path")

    args, kwargs = mock_get.call_args
    assert args[0] == "http://93.184.216.34/path"
    assert kwargs["headers"]["Host"] == "example.com"
    assert kwargs["allow_redirects"] is False


def test_safe_get_rejects_redirect_loop():
    from sherpa_ai.utils import safe_get

    loop = _redirect_response("http://loop.example/again")
    with patch("socket.getaddrinfo", return_value=[(None, None, None, "", ("93.184.216.34", 0))]), \
         patch("requests.get", return_value=loop):
        with pytest.raises(UnsafeURLError):
            safe_get("http://loop.example")


def test_safe_get_prefers_ipv4_and_falls_back_on_connection_error():
    # A host with both an IPv4 and IPv6 address must be tried IPv4-first, and
    # if that connection fails, the next validated address should be tried
    # rather than the whole fetch failing outright.
    from sherpa_ai.utils import safe_get

    final = Mock()
    final.status_code = 200
    addrinfo = [
        (None, None, None, "", ("2606:2800:220:1:248:1893:25c8:1946", 0)),
        (None, None, None, "", ("93.184.216.34", 0)),
    ]
    with patch("socket.getaddrinfo", return_value=addrinfo), \
         patch(
             "requests.get",
             side_effect=[requests.exceptions.ConnectionError("unreachable"), final],
         ) as mock_get:
        result = safe_get("http://example.com/path")

    assert result is final
    assert mock_get.call_count == 2
    first_url = mock_get.call_args_list[0].args[0]
    second_url = mock_get.call_args_list[1].args[0]
    assert first_url == "http://93.184.216.34/path"  # IPv4 tried first
    assert second_url == "http://[2606:2800:220:1:248:1893:25c8:1946]/path"


def test_safe_get_raises_when_all_validated_addresses_unreachable():
    from sherpa_ai.utils import safe_get

    with patch("socket.getaddrinfo", return_value=[(None, None, None, "", ("93.184.216.34", 0))]), \
         patch("requests.get", side_effect=requests.exceptions.ConnectionError("down")):
        with pytest.raises(UnsafeURLError):
            safe_get("http://example.com")


def test_safe_get_host_header_excludes_userinfo():
    # The Host header must be built from hostname[:port] only — parsed.netloc
    # can carry "user:pass@host" userinfo, which must never leak into the
    # header sent to the (validated) remote server.
    from sherpa_ai.utils import safe_get

    final = Mock()
    final.status_code = 200
    with patch("socket.getaddrinfo", return_value=[(None, None, None, "", ("93.184.216.34", 0))]), \
         patch("requests.get", return_value=final) as mock_get:
        safe_get("http://user:secret@example.com/path")

    _, kwargs = mock_get.call_args
    assert kwargs["headers"]["Host"] == "example.com"
    assert "secret" not in kwargs["headers"]["Host"]


def test_chunk_and_summarize_with_completion_llm():
    # chunk_and_summarize must call the LLM once per chunk and return the
    # summaries as plain strings (not message objects), regardless of the
    # underlying langchain LLM API.
    llm = FakeListLLM(responses=["summary of the page"])
    result = chunk_and_summarize(
        text_data="Some short text about the weather.",
        question="What is the weather?",
        link="https://example.com",
        llm=llm,
    )
    assert result == "summary of the page"


def test_chunk_and_summarize_with_chat_llm():
    # Chat models return AIMessage from invoke; the summary must still be a
    # plain string so downstream token counting/joining keeps working.
    llm = FakeListChatModel(responses=["chat summary of the page"])
    result = chunk_and_summarize(
        text_data="Some short text about the weather.",
        question="What is the weather?",
        link="https://example.com",
        llm=llm,
    )
    assert isinstance(result, str)
    assert result == "chat summary of the page"


def test_chunk_and_summarize_file_with_chat_llm():
    llm = FakeListChatModel(responses=["file summary"])
    result = chunk_and_summarize_file(
        text_data="Contents of a small file.",
        question="What is in the file?",
        file_name="notes.txt",
        file_format="txt",
        llm=llm,
        title="Notes",
    )
    assert isinstance(result, str)
    assert result == "file summary"
