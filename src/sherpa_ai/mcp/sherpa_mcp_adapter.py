import asyncio
import json
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional, Type

from pydantic import Field
from sherpa_ai.actions.base import AsyncBaseAction
from langchain_core.language_models import BaseLanguageModel
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPServerToolsToSherpaActions:
    """
    Adapter class that connects to an MCP server, retrieves available tools, and dynamically creates Sherpa-compatible actions for each tool.

    This class enables seamless integration of external MCP server tools into the Sherpa agent framework by:
      - Establishing a connection to an MCP server (e.g., GitHub, Linear, Notion, etc.)
      - Listing all available tools exposed by the server
      - Dynamically generating Sherpa AsyncBaseAction subclasses for each tool, with correct argument signatures and descriptions
      - Providing a unified interface for executing these tools as Sherpa actions

    Attributes:
        llm (BaseLanguageModel): The language model to be used by the actions.
        server_command (str): The command to start/connect to the MCP server.
        server_args (List[str]): Arguments for the server command.
        env (dict): Environment variables for the server process.
        actions (List[AsyncBaseAction]): List of dynamically created Sherpa actions.

    Example:
        >>> adapter = MCPServerToolsToSherpaActions(llm, server_command="bash", server_args=["github-mcp-server.sh"])
        >>> await adapter.connect()
        >>> actions = adapter.actions
        >>> result = await actions[0].execute(...)

    Methods:
        connect(): Connects to the MCP server and creates Sherpa actions for each tool.
        close(): Closes the connection and cleans up resources.
    """
    def __init__(self, llm: BaseLanguageModel, server_command: str, server_args: Optional[List[str]] = None, env=None):
        self.llm = llm
        self.server_command = server_command
        self.server_args = server_args or []
        self.env = env
        self.exit_stack = AsyncExitStack()
        self.stdio = None
        self.stdin = None
        self.session: Optional[ClientSession] = None
        self.tools = []
        self.actions: List[AsyncBaseAction] = []

    async def connect(self):
        server_params = StdioServerParameters(
            command=self.server_command,
            args=self.server_args,
            env=self.env,
        )
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.stdin = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.stdin))
        await self.session.initialize()
        response = await self.session.list_tools()
        self.tools = response.tools
        self._create_actions_from_tools()
        return self.actions

    def _create_actions_from_tools(self):
        self.actions = []
        for tool in self.tools:
            action_cls = self._make_action_class(tool)
            action_instance = action_cls(llm=self.llm, session=self.session)
            self.actions.append(action_instance)

    def _parse_args_from_tool(self, tool):
        if hasattr(tool, 'inputSchema') and tool.inputSchema and 'properties' in tool.inputSchema:
            return {k: v.get('description', '') for k, v in tool.inputSchema['properties'].items()}
        desc = getattr(tool, 'description', '')
        args = {}
        if desc:
            for line in desc.split('\n'):
                if ':' in line:
                    k, v = line.split(':', 1)
                    args[k.strip()] = v.strip()
        return args

    def _make_action_class(self, tool):
        args = self._parse_args_from_tool(tool)
        name = tool.name
        description = getattr(tool, 'description', '')
        
        async def execute(self, **kwargs):
            if not self.session:
                return "Error: Not connected to MCP server."
            try:
                result = await self.session.call_tool(self.name, kwargs)
                content = result.content
                if content and hasattr(content[0], "text"):
                    try:
                        return json.loads(content[0].text)
                    except Exception:
                        return content[0].text
                elif content and isinstance(content[0], str):
                    try:
                        return json.loads(content[0])
                    except Exception:
                        return content[0]
                return content
            except Exception as e:
                return f"Error executing tool {self.name}: {e}"

        # Add type annotations for Pydantic compatibility
        annotations = {
            "name": str,
            "args": dict,
            "usage": str,
            "llm": BaseLanguageModel,
            "session": Any,
        }

        action_cls = type(
            name,
            (AsyncBaseAction,),
            {
                "__annotations__": annotations,
                "name": name,
                "args": args,
                "usage": description,
                "llm": None,
                "session": None,
                "execute": execute,
            },
        )
        return action_cls

    async def close(self):
        try:
            await self.exit_stack.aclose()
        except (asyncio.CancelledError, GeneratorExit):
            print("MCP client cleanup cancelled (suppressed CancelledError/GeneratorExit)")
        except Exception as e:
            print(f"Warning: Error during MCP client cleanup: {e}")
        finally:
            self.session = None 