import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from sherpa_ai.actions.sherpa_mcp_adapter import MCPServerToolsToSherpaActions
from sherpa_ai.actions.base import BaseAction, AsyncBaseAction
from langchain_core.language_models.base import BaseLanguageModel

class DummySession:
    async def call_tool(self, name, kwargs):
        class Result:
            def __init__(self, content):
                self.content = content
        if name == "fail_tool":
            raise Exception("fail")
        return Result([json.dumps({"result": "ok"})])

class DummyLLM(BaseLanguageModel):
    def __init__(self):
        super().__init__()
    def ainvoke(self, *args, **kwargs):
        pass
    def agenerate_prompt(self, *args, **kwargs):
        pass
    def apredict(self, *args, **kwargs):
        pass
    def apredict_messages(self, *args, **kwargs):
        pass
    def generate_prompt(self, *args, **kwargs):
        pass
    def invoke(self, *args, **kwargs):
        pass
    def predict(self, *args, **kwargs):
        pass
    def predict_messages(self, *args, **kwargs):
        pass

@pytest.fixture
def mock_llm():
    return DummyLLM()

@pytest.fixture
def mock_tool():
    tool = MagicMock()
    tool.name = "test_tool"
    tool.description = "A test tool"
    tool.inputSchema = {
        "properties": {
            "foo": {"type": "string", "description": "A foo param"}
        }
    }
    return tool

@pytest.fixture
def mock_tool_no_schema():
    tool = MagicMock()
    tool.name = "test_tool"
    tool.description = "foo: A foo param\nbar: A bar param"
    tool.inputSchema = None
    return tool

@pytest.fixture
def mock_session():
    return DummySession()

@pytest.fixture
def adapter(mock_llm):
    return MCPServerToolsToSherpaActions(
        llm=mock_llm,
        server_command="echo",
        server_args=["foo"]
    )

class TestMCPServerToolsToSherpaActions:
    def test_parse_args_from_tool_with_input_schema(self, adapter, mock_tool):
        args = adapter._parse_args_from_tool(mock_tool)
        assert "foo" in args
        assert args["foo"] == "A foo param"

    def test_parse_args_from_tool_without_input_schema(self, adapter, mock_tool_no_schema):
        args = adapter._parse_args_from_tool(mock_tool_no_schema)
        assert "foo" in args
        assert "bar" in args
        assert args["foo"] == "A foo param"
        assert args["bar"] == "A bar param"

    def test_make_action_class(self, adapter, mock_tool, mock_llm):
        ActionClass = adapter._make_action_class(mock_tool)
        action = ActionClass(name="test_tool", args={}, usage="desc", llm=mock_llm, session=None)
        assert issubclass(ActionClass, AsyncBaseAction)
        assert action.name == "test_tool"
        assert hasattr(action, "execute")

    @pytest.mark.asyncio
    async def test_action_execution_success(self, adapter, mock_tool, mock_session, mock_llm):
        ActionClass = adapter._make_action_class(mock_tool)
        action = ActionClass(name="test_tool", args={}, usage="desc", llm=mock_llm, session=mock_session)
        result = await action.execute(foo="bar")
        assert result["result"] == "ok"

    @pytest.mark.asyncio
    async def test_action_execution_failure(self, adapter, mock_tool, mock_session, mock_llm):
        fail_tool = MagicMock()
        fail_tool.name = "fail_tool"
        fail_tool.description = "desc"
        fail_tool.inputSchema = {"properties": {}}
        ActionClass = adapter._make_action_class(fail_tool)
        action = ActionClass(name="fail_tool", args={}, usage="desc", llm=mock_llm, session=mock_session)
        result = await action.execute()
        assert "Error executing tool fail_tool" in result

    @pytest.mark.asyncio
    async def test_action_execution_no_session(self, adapter, mock_tool, mock_llm):
        ActionClass = adapter._make_action_class(mock_tool)
        action = ActionClass(name="test_tool", args={}, usage="desc", llm=mock_llm, session=None)
        result = await action.execute(foo="bar")
        assert "Error: Not connected to MCP server." in result

    def test_create_actions_from_tools(self, adapter, mock_tool, mock_llm):
        # Use object.__setattr__ to avoid Pydantic validation
        object.__setattr__(adapter, "tools", [mock_tool])
        adapter._create_actions_from_tools()
        assert len(adapter.actions) == 1
        action = adapter.actions[0]
        assert isinstance(action, AsyncBaseAction)
        assert action.name == "test_tool"

    def test_execute_success(self, adapter):
        with patch('sherpa_ai.actions.sherpa_mcp_adapter.stdio_client') as mock_stdio_client, \
             patch('sherpa_ai.actions.sherpa_mcp_adapter.ClientSession') as mock_client_session:
            
            class DummyAsyncContext:
                async def __aenter__(self):
                    return ("dummy_stdio", "dummy_stdin")
                async def __aexit__(self, exc_type, exc, tb):
                    pass
            
            class DummySessionContext:
                async def __aenter__(self):
                    return dummy_session
                async def __aexit__(self, exc_type, exc, tb):
                    pass
            
            dummy_session = MagicMock()
            dummy_session.initialize = AsyncMock()
            dummy_session.list_tools = AsyncMock()
            dummy_session.list_tools.return_value.tools = [MagicMock(name="test_tool")]
            
            mock_stdio_client.return_value = DummyAsyncContext()
            mock_client_session.return_value = DummySessionContext()
            
            def fake_create_actions(*args, **kwargs):
                mock_action = MagicMock()
                mock_action.name = "test_tool"
                object.__setattr__(adapter, "actions", [mock_action])
                return adapter.actions
            
            with patch.object(adapter, "_create_actions_from_tools", side_effect=fake_create_actions):
                result = adapter.execute()
                assert result["status"] == "success"
                assert len(result["actions"]) == 1
                assert result["actions"][0].name == "test_tool"

    def test_execute_missing_server_command(self, adapter):
        object.__setattr__(adapter, "server_command", "")
        result = adapter.execute()
        assert result["status"] == "error"
        assert "server_command is required" in result["error"]

    def test_execute_connection_error(self, adapter):
        with patch('sherpa_ai.actions.sherpa_mcp_adapter.stdio_client') as mock_stdio_client:
            mock_stdio_client.side_effect = Exception("Connection failed")
            result = adapter.execute()
            assert result["status"] == "error"
            assert "Connection failed" in result["error"] 
            