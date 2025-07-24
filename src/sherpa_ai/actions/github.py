import asyncio
import json
import os
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional

from langchain_core.language_models import BaseLanguageModel
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import Field

from sherpa_ai.actions.base import AsyncBaseAction
from sherpa_ai.actions.linear import LinearAction


class GithubAction(AsyncBaseAction):
    name: str = "Github Action"
    args: dict = {
        "operation": "The operation to perform (e.g., 'analyze_repository_prs', 'list_pull_requests', 'get_pull_request_files')",
        "owner": "The repository owner",
        "repo": "The repository name",
        "pull_number": "The pull request number",
    }
    usage: str = "Used to interact with the Github API"
    llm: BaseLanguageModel
    linear_action: Optional[LinearAction] = None
    session: Optional[ClientSession] = Field(None, exclude=True)
    exit_stack: AsyncExitStack = Field(default_factory=AsyncExitStack, exclude=True)
    tools: list = Field(default_factory=list, exclude=True)
    stdio: Any = Field(None, exclude=True)
    stdin: Any = Field(None, exclude=True)

    async def connect_to_server(self, server_script_path: str):
        """Connect to the GitHub MCP server.

        Args:
            server_script_path: Path to the GitHub MCP server script
        """
        if server_script_path.endswith(".sh"):
            command = "bash"
        elif server_script_path.endswith(".py"):
            command = "python"
        else:
            command = server_script_path
            server_script_path = None

        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path] if server_script_path else [],
            env=None,
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
            "\nConnected to GitHub MCP server with tools:",
            [tool.name for tool in self.tools],
        )
        return self.tools

    def parse_mcp_response(self, content) -> Any:
        """Helper to robustly parse MCP server responses."""
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
        """Call a tool on the GitHub MCP server."""
        if not self.session:
            raise ValueError("Not connected to server. Call connect_to_server first.")

        result = await self.session.call_tool(tool_name, parameters)
        return self.parse_mcp_response(result.content)

    async def analyze_pr_with_llm(self, pr_title: str, file_changes: List[str]) -> str:
        """Analyze PR title accuracy using LLM."""
        prompt = f"""
        Given the following pull request title and the list of changed files, does the title accurately describe the changes? Reply 'Yes' or 'No' and explain your reasoning.

        Title: {pr_title}
        Changed files: {file_changes}
        """
        try:
            response = await self.llm.ainvoke(prompt)
            return response.content
        except Exception as e:
            return f"Error analyzing PR: {e}"

    async def list_pull_requests(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """List pull requests for a repository."""
        return await self.call_tool(
            "list_pull_requests", {"owner": owner, "repo": repo}
        )

    async def get_pull_request_files(
        self,
        owner: str,
        repo: str,
        pull_number: int,
        page: int = 1,
        per_page: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get files changed in a pull request."""
        return await self.call_tool(
            "get_pull_request_files",
            {
                "owner": owner,
                "repo": repo,
                "pull_number": pull_number,
                "page": page,
                "perPage": per_page,
            },
        )

    async def get_pull_request(
        self, owner: str, repo: str, pull_number: int
    ) -> Dict[str, Any]:
        """Get detailed information about a specific pull request."""
        return await self.call_tool(
            "get_pull_request",
            {"owner": owner, "repo": repo, "pull_number": pull_number},
        )

    async def get_repository_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository information."""
        return await self.call_tool("get_repository", {"owner": owner, "repo": repo})

    async def analyze_repository_prs(self, owner: str, repo: str) -> None:
        """Analyze all pull requests in a repository."""
        print(f"\nAnalyzing pull requests for {owner}/{repo}...")

        # Get PRs
        prs = await self.list_pull_requests(owner, repo)
        print(f"Found {len(prs)} pull requests.")

        for pr in prs:
            pr_number = pr.get("number")
            pr_title = pr.get("title")
            pr_state = pr.get("state")

            print(f"\nPR #{pr_number}: {pr_title} (State: {pr_state})")

            # Get file changes for this PR
            try:
                files_content = await self.get_pull_request_files(
                    owner, repo, pr_number
                )

                if isinstance(files_content, list):
                    file_changes = [f.get("filename") for f in files_content]
                else:
                    file_changes = files_content

                print(f"Changed files: {file_changes}")

                llm_result = await self.analyze_pr_with_llm(pr_title, file_changes)
                print(f"LLM analysis: {llm_result}")

                if self.linear_action:
                    await self.linear_action.execute(
                        operation="process_pr_for_linear",
                        pr_data=pr,
                        file_changes=file_changes,
                    )

            except Exception as e:
                print(f"Error analyzing PR #{pr_number}: {e}")

    async def close(self):
        """Close the client session."""
        try:
            await self.exit_stack.aclose()
        except asyncio.CancelledError:
            print("GitHub client cleanup cancelled")
        except Exception as e:
            print(f"Warning: Error during GitHub client cleanup: {e}")
        finally:
            self.session = None

    async def execute(self, operation: str, **kwargs) -> str:
        owner = kwargs.get("owner")
        repo = kwargs.get("repo")
        pull_number = kwargs.get("pull_number")

        if operation == "analyze_repository_prs":
            if not owner or not repo:
                return "Error: 'owner' and 'repo' are required for 'analyze_repository_prs'."
            await self.analyze_repository_prs(owner, repo)
            return "Analyzed all pull requests."
        elif operation == "list_pull_requests":
            if not owner or not repo:
                return "Error: 'owner' and 'repo' are required for 'list_pull_requests'."
            return await self.list_pull_requests(owner, repo)
        elif operation == "get_pull_request_files":
            if not owner or not repo or not pull_number:
                return "Error: 'owner', 'repo', and 'pull_number' are required for 'get_pull_request_files'."
            return await self.get_pull_request_files(owner, repo, pull_number)
        else:
            return f"Unknown operation: {operation}"