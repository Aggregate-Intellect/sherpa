import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Optional, Any
from sherpa_ai.agents.pr_analyzer_agent import PRAnalyzerAgent
from sherpa_ai.models.sherpa_base_chat_model import SherpaBaseChatModel
from sherpa_ai.memory import Belief, SharedMemory
from sherpa_ai.policies.base import BasePolicy
from sherpa_ai.actions.base import AsyncBaseAction


class MockAction(AsyncBaseAction):
    """Mock action for testing."""

    name: str
    args: dict = {}
    usage: str = ""
    llm: Optional[Any] = None
    session: Optional[Any] = None

    def __init__(self, name: str, **kwargs):
        super().__init__(name=name, **kwargs)
        self._execute_mock = AsyncMock()

    async def execute(self, **kwargs):
        """Mock execute method."""
        return await self._execute_mock(**kwargs)


class TestPRAnalyzerAgent:
    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM for testing."""
        llm = MagicMock(spec=SherpaBaseChatModel)
        llm.ainvoke = AsyncMock()
        llm.get_num_tokens = MagicMock(return_value=1000)
        return llm

    @pytest.fixture
    def mock_actions(self):
        """Create mock actions for testing."""
        actions = []

        list_prs_action = MockAction("list_pull_requests")
        actions.append(list_prs_action)

        get_files_action = MockAction("get_pull_request_files")
        actions.append(get_files_action)

        list_issues_action = MockAction("list_issues")
        actions.append(list_issues_action)

        create_comment_action = MockAction("create_comment")
        actions.append(create_comment_action)

        return actions

    @pytest.fixture
    def mock_belief(self):
        """Create a mock belief for testing."""
        belief = MagicMock(spec=Belief)
        belief.current_task = MagicMock()
        belief.current_task.content = "Test task"
        belief.get_context = MagicMock(return_value="Test context")
        belief.get_internal_history = MagicMock(return_value="Test history")
        return belief

    @pytest.fixture
    def mock_shared_memory(self):
        """Create a mock shared memory for testing."""
        return MagicMock(spec=SharedMemory)

    @pytest.fixture
    def mock_policy(self):
        """Create a mock policy for testing."""
        return MagicMock(spec=BasePolicy)

    @pytest.fixture
    def agent(
        self, mock_llm, mock_actions, mock_belief, mock_shared_memory, mock_policy
    ):
        """Create a PRAnalyzerAgent instance for testing."""
        return PRAnalyzerAgent(
            llm=mock_llm,
            actions=mock_actions,
            belief=mock_belief,
            shared_memory=mock_shared_memory,
            policy=mock_policy,
        )

    def test_extract_linear_id(self, agent):
        """Test the extract_linear_id method with various patterns."""
        assert agent.extract_linear_id("MCP-123") == "MCP-123"
        assert agent.extract_linear_id("[MCP-456]") == "MCP-456"
        assert agent.extract_linear_id("(MCP-789)") == "MCP-789"
        assert agent.extract_linear_id("MCP-101: Some description") == "MCP-101"

        assert agent.extract_linear_id("mcp-123") == "MCP-123"
        assert agent.extract_linear_id("[mcp-456]") == "MCP-456"

        assert agent.extract_linear_id("No Linear ID here") is None
        assert agent.extract_linear_id("") is None
        assert agent.extract_linear_id(None) is None

    @pytest.mark.asyncio
    async def test_analyze_repository_prs_success(self, agent, mock_llm):
        """Test successful PR analysis workflow."""
        mock_prs = [
            {
                "number": 1,
                "title": "MCP-123: Fix bug in login",
                "body": "This PR fixes a critical bug in the login system",
                "html_url": "https://github.com/owner/repo/pull/1",
            },
            {
                "number": 2,
                "title": "Add new feature",
                "body": "No Linear ID in this PR",
                "html_url": "https://github.com/owner/repo/pull/2",
            },
        ]

        mock_files = [{"filename": "src/auth.py"}, {"filename": "tests/test_auth.py"}]

        mock_issues = [
            {
                "id": "linear-issue-123",
                "identifier": "MCP-123",
                "title": "Fix login bug",
            }
        ]

        mock_llm.ainvoke.return_value.content = (
            "This PR looks good and addresses the issue properly."
        )

        agent.action_map["list_pull_requests"]._execute_mock.return_value = mock_prs
        agent.action_map[
            "get_pull_request_files"
        ]._execute_mock.return_value = mock_files
        agent.action_map["list_issues"]._execute_mock.return_value = mock_issues
        agent.action_map["create_comment"]._execute_mock.return_value = {
            "success": True
        }

        result = await agent.analyze_repository_prs("owner", "repo")

        assert "PR #1: Comment posted to Linear MCP-123" in result
        assert "PR #2: No Linear ID found" in result

        agent.action_map["list_pull_requests"]._execute_mock.assert_called_once_with(
            owner="owner", repo="repo"
        )
        assert agent.action_map["get_pull_request_files"]._execute_mock.call_count == 2
        agent.action_map["get_pull_request_files"]._execute_mock.assert_any_call(
            owner="owner", repo="repo", pull_number=1
        )
        agent.action_map["get_pull_request_files"]._execute_mock.assert_any_call(
            owner="owner", repo="repo", pull_number=2
        )
        agent.action_map["list_issues"]._execute_mock.assert_called_once()
        agent.action_map["create_comment"]._execute_mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_repository_prs_missing_actions(self, agent):
        """Test PR analysis when required actions are missing."""
        agent.action_map = {}

        result = await agent.analyze_repository_prs("owner", "repo")
        assert "Error: Required MCP actions not found" in result

    @pytest.mark.asyncio
    async def test_analyze_repository_prs_invalid_prs_response(self, agent):
        """Test PR analysis when PRs response is invalid."""
        agent.action_map[
            "list_pull_requests"
        ]._execute_mock.return_value = "Invalid response"

        result = await agent.analyze_repository_prs("owner", "repo")
        assert "Error: Unexpected PRs response" in result

    @pytest.mark.asyncio
    async def test_analyze_repository_prs_linear_issue_not_found(self, agent, mock_llm):
        """Test PR analysis when Linear issue is not found."""
        mock_prs = [
            {
                "number": 1,
                "title": "MCP-999: Some PR",
                "body": "Description",
                "html_url": "https://github.com/owner/repo/pull/1",
            }
        ]

        mock_files = [{"filename": "src/file.py"}]
        mock_issues = []

        mock_llm.ainvoke.return_value.content = "Analysis content"

        agent.action_map["list_pull_requests"]._execute_mock.return_value = mock_prs
        agent.action_map[
            "get_pull_request_files"
        ]._execute_mock.return_value = mock_files
        agent.action_map["list_issues"]._execute_mock.return_value = mock_issues

        result = await agent.analyze_repository_prs("owner", "repo")

        assert "PR #1: Linear issue MCP-999 not found" in result

    def test_agent_initialization(
        self, mock_llm, mock_actions, mock_belief, mock_shared_memory, mock_policy
    ):
        """Test agent initialization with proper attributes."""
        agent = PRAnalyzerAgent(
            llm=mock_llm,
            actions=mock_actions,
            belief=mock_belief,
            shared_memory=mock_shared_memory,
            policy=mock_policy,
        )

        assert agent.name == "PR Analyzer Agent"
        assert "analyzing GitHub PRs" in agent.description
        assert len(agent.action_map) == 4
        assert "list_pull_requests" in agent.action_map
        assert "get_pull_request_files" in agent.action_map
        assert "list_issues" in agent.action_map
        assert "create_comment" in agent.action_map
