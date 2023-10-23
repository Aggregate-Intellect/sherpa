import pytest

from sherpa_ai.output_parser import TaskAction, TaskOutputParser, preprocess_json_input


@pytest.mark.parametrize(
    "input_str, expected_output",
    [
        ('{"name": "John\\Doe"}', '{"name": "John\\\\Doe"}'),  # Test with escaped backslash
        ('{"age": 30, "city": "New\\York"}', '{"age": 30, "city": "New\\\\York"}'),  # Test with escaped backslash
        ('{"message": "Hello\\\\nWorld"}', '{"message": "Hello\\\\nWorld"}'),  # Test with newline escape
        ('{"key": "value"}', '{"key": "value"}'),  # Test without any backslash to escape
    ],
)
def test_preprocess_json_input(input_str, expected_output):
    result = preprocess_json_input(input_str)
    assert result == expected_output

# Test cases for TaskOutputParser class
@pytest.mark.parametrize(
    "text, expected_action",
    [
        ('{"command": {"name": "foo", "args": {"arg1": "value1"}}}', TaskAction(name="foo", args={"arg1": "value1"})),
        ('{"command": {"name": "bar", "args": {"arg2": "value2"}}}', TaskAction(name="bar", args={"arg2": "value2"})),
        ('{"invalid_key": "value"}', TaskAction(name="ERROR", args={"error": "Incomplete command args: {'invalid_key': 'value'}"})),
        ('not_a_json_string', TaskAction(name="ERROR", args={"error": "Could not parse invalid json: not_a_json_string"})),
    ],
)
def test_TaskOutputParser_parse(text, expected_action):
    parser = TaskOutputParser()
    result = parser.parse(text)
    assert result == expected_action
