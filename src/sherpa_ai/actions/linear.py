import asyncio
import json
import os
import re
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional

from langchain_core.language_models import BaseLanguageModel
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import Field

from sherpa_ai.actions.base import AsyncBaseAction


class LinearAction(AsyncBaseAction):
    name: str = "Linear Action"
    args: dict = {
        "operation": "The operation to perform (e.g., 'get_issue', 'search_issues', 'create_comment', 'process_pr_for_linear')",
        "issue_id": "The ID of the Linear issue",
        "query": "The search query for issues",
        "body": "The body of the comment to create",
        "pr_data": "The pull request data",
        "file_changes": "The file changes in the pull request",
    }
    usage: str = "Used to interact with the Linear API"
    llm: BaseLanguageModel
    session: Optional[ClientSession] = Field(None, exclude=True)
    exit_stack: AsyncExitStack = Field(default_factory=AsyncExitStack, exclude=True)
    tools: list = Field(default_factory=list, exclude=True)
    stdio: Any = Field(None, exclude=True)
    stdin: Any = Field(None, exclude=True)

    async def connect_to_server(self):
        """Connect to the Linear MCP server via remote SSE."""
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "mcp-remote", "https://mcp.linear.app/sse"],
            env=os.environ,
        )

        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.stdio, self.stdin = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.stdin)
        )
        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        self.tools = response.tools
        print(
            "\nConnected to Linear MCP server with tools:",
            [tool.name for tool in self.tools],
        )
        return self.tools

    def parse_mcp_response(self, content) -> Any:
        """Helper to robustly parse MCP server responses."""
        print(f"Raw Linear MCP response: {content}")
        if not content:
            return []

        if hasattr(content[0], "text"):
            try:
                return json.loads(content[0].text)
            except Exception:
                return content[0].text
        elif isinstance(content[0], str):
            try:
                return json.loads(content[0])
            except Exception:
                return content[0]
        return content

    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Call a tool on the Linear MCP server."""
        if not self.session:
            raise ValueError("Not connected to server. Call connect_to_server first.")

        result = await self.session.call_tool(tool_name, parameters)
        return self.parse_mcp_response(result.content)

    def extract_linear_id(self, text: str) -> Optional[str]:
        """Extract Linear issue ID from PR title or description.

        Looks for patterns like:
        - MCP-123
        - [MCP-123]
        - (MCP-123)
        - MCP-123:
        """
        if not text:
            return None

        # Pattern to match MCP-[number] with optional brackets/parentheses
        patterns = [
            r"MCP-(\d+)",
            r"\[MCP-(\d+)\]",
            r"\(MCP-(\d+)\)",
            r"MCP-(\d+):",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return f"MCP-{match.group(1)}"

        return None

    async def get_issue(self, issue_id: str) -> Dict[str, Any]:
        """Get Linear issue by ID."""
        try:
            return await self.call_tool("get_issue", {"id": issue_id})
        except Exception as e:
            print(f"Error getting issue {issue_id}: {e}")
            return {}

    async def search_issues(self, query: str) -> List[Dict[str, Any]]:
        """Search Linear issues."""
        try:
            return await self.call_tool("search_issues", {"query": query})
        except Exception as e:
            print(f"Error searching issues with query '{query}': {e}")
            return []

    async def debug_linear_issue(self, issue_id: str) -> None:
        """Debug method to understand Linear issue structure."""
        print(f"🔍 Debugging Linear issue: {issue_id}")

        try:
            issues = await self.call_tool("list_issues", {})

            if isinstance(issues, list):
                print(f"Found {len(issues)} total issues")
                for i, issue in enumerate(issues[:5]): 
                    print(
                        f"  Issue {i+1}: {issue.get('identifier', 'No identifier')} - {issue.get('title', 'No title')}"
                    )
                    if issue.get("identifier") == issue_id:
                        print(f"  ✅ Found target issue! Internal ID: {issue.get('id')}")
                        return issue
            else:
                print(f"Issues response type: {type(issues)}")
                print(f"Issues response: {issues}")

            direct_issue = await self.call_tool("get_issue", {"id": issue_id})
            print(f"Direct get_issue result: {direct_issue}")

        except Exception as e:
            print(f"Error during debug: {e}")

        return None

    async def create_comment(self, issue_id: str, body: str) -> Dict[str, Any]:
        """Create a comment on a Linear issue."""
        try:
            result = await self.call_tool(
                "create_comment", {"issueId": issue_id, "body": body}
            )
            print(f"Raw create_comment response: {result}")
            return result if result else {"success": True}
        except Exception as e:
            print(f"Error creating comment on issue {issue_id}: {e}")
            return {}

    async def generate_pr_analysis_comment(
        self,
        pr_title: str,
        pr_description: str,
        file_changes: List[str],
        pr_url: str = None,
    ) -> str:
        """Generate a comprehensive PR analysis comment using LLM."""
        prompt = f"""
        You are a code reviewer analyzing a pull request. Generate a helpful comment for the Linear issue based on the PR information.

        PR Title: {pr_title}
        PR Description: {pr_description or "No description provided"}
        Changed Files: {file_changes}
        {f"PR URL: {pr_url}" if pr_url else ""}

        Please provide:
        1. A brief summary of what the PR does
        2. Key files changed and their purpose
        3. Any observations about the scope of changes
        4. Whether the PR seems to address the issue appropriately

        Keep the comment professional, constructive, and focused on the technical aspects.
        """

        try:
            response = await self.llm.ainvoke(prompt)
            return response.content
        except Exception as e:
            return f"Error generating PR analysis: {e}"

    async def process_pr_for_linear(
        self, pr_data: Dict[str, Any], file_changes: List[str]
    ) -> bool:
        """Process a PR and create a Linear comment if a Linear ID is found."""
        pr_title = pr_data.get("title", "")
        pr_description = pr_data.get("body", "")
        pr_number = pr_data.get("number")
        pr_url = pr_data.get("html_url")

        # Extract Linear ID from title or description
        linear_id = self.extract_linear_id(pr_title) or self.extract_linear_id(
            pr_description
        )

        if not linear_id:
            print(f"No Linear ID found in PR #{pr_number}: {pr_title}")
            return False

        print(f"Found Linear ID: {linear_id} in PR #{pr_number}")

        await self.debug_linear_issue(linear_id)

        print(f"Searching for Linear issue with ID: {linear_id}")

        try:
            issues = await self.call_tool("list_issues", {})
            target_issue = None

            if isinstance(issues, list):
                for issue in issues:
                    if issue.get("identifier") == linear_id:
                        target_issue = issue
                        break

            if not target_issue:
                print(f"Linear issue {linear_id} not found in issue list")
                return False

            print(
                f"Found Linear issue: {target_issue.get('title', 'No title')} (ID: {target_issue.get('id')})"
            )
            comment_body = await self.generate_pr_analysis_comment(
                pr_title, pr_description, file_changes, pr_url
            )

            comment_with_pr_ref = f"## PR Update: #{pr_number}\n\n{comment_body}\n\n---\n*This comment was automatically generated based on PR #{pr_number}*"

            print(
                f"Creating comment on Linear issue {linear_id} (internal ID: {target_issue.get('id')})"
            )
            comment_result = await self.create_comment(
                target_issue.get("id"), comment_with_pr_ref
            )

            if comment_result:
                print(f"Successfully created comment on Linear issue {linear_id}")
                return True
            else:
                print(f"Failed to create comment on Linear issue {linear_id}")
                return False

        except Exception as e:
            print(f"Error processing Linear issue {linear_id}: {e}")
            return False

    async def close(self):
        """Close the client session."""
        try:
            await self.exit_stack.aclose()
        except asyncio.CancelledError:
            print("Linear client cleanup cancelled")
        except Exception as e:
            print(f"Warning: Error during Linear client cleanup: {e}")
        finally:
            self.session = None

    async def execute(self, operation: str, **kwargs) -> str:
        issue_id = kwargs.get("issue_id")
        query = kwargs.get("query")
        body = kwargs.get("body")
        pr_data = kwargs.get("pr_data")
        file_changes = kwargs.get("file_changes")

        if operation == "get_issue":
            if not issue_id:
                return "Error: 'issue_id' is required for 'get_issue'."
            return await self.get_issue(issue_id)
        elif operation == "search_issues":
            if not query:
                return "Error: 'query' is required for 'search_issues'."
            return await self.search_issues(query)
        elif operation == "create_comment":
            if not issue_id or not body:
                return "Error: 'issue_id' and 'body' are required for 'create_comment'."
            return await self.create_comment(issue_id, body)
        elif operation == "process_pr_for_linear":
            if not pr_data or not file_changes:
                return "Error: 'pr_data' and 'file_changes' are required for 'process_pr_for_linear'."
            return await self.process_pr_for_linear(pr_data, file_changes)
        else:
            return f"Unknown operation: {operation}"