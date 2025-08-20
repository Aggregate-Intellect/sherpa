import asyncio
import json
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional, Type

from pydantic import Field
from sherpa_ai.actions.base import BaseAction, AsyncBaseAction
from langchain_core.language_models import BaseLanguageModel
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPServerToolsToSherpaActions(BaseAction):
    """
    Action that connects to an MCP server, retrieves available tools, and dynamically creates Sherpa-compatible actions for each tool.

    This action enables seamless integration of external MCP server tools into the Sherpa agent framework by:
      - Establishing a connection to an MCP server (e.g., GitHub, Linear, Notion, etc.)
      - Listing all available tools exposed by the server
      - Dynamically generating Sherpa AsyncBaseAction subclasses for each tool, with correct argument signatures and descriptions
      - Providing a unified interface for executing these tools as Sherpa actions

    Attributes:
        name (str): The name of the action.
        args (dict): Arguments for the action including server_command, server_args, and env.
        usage (str): Description of how to use the action.
        llm (BaseLanguageModel): The language model to be used by the created actions.
        server_command (str): The command to start/connect to the MCP server.
        server_args (List[str]): Arguments for the server command.
        env (dict): Environment variables for the server process.
        actions (List[AsyncBaseAction]): List of dynamically created Sherpa actions.

    Example:
        >>> adapter = MCPServerToolsToSherpaActions(
        ...     name="github_mcp_adapter",
        ...     args={"server_command": "bash", "server_args": ["github-mcp-server.sh"]},
        ...     usage="Connects to GitHub MCP server and creates actions",
        ...     llm=llm
        ... )
        >>> result = await adapter.execute()
        >>> actions = result["actions"]
    """
    
    name: str = "mcp_server_tools_to_sherpa_actions"
    args: dict = {
        "server_command": "Command to start the MCP server",
        "server_args": "Arguments for the server command",
        "env": "Environment variables for the server process"
    }
    usage: str = "Connects to an MCP server and converts its tools to Sherpa actions"
    
    # Define these as Pydantic fields
    server_command: str = Field(default="", description="Command to start the MCP server")
    server_args: List[str] = Field(default_factory=list, description="Arguments for the server command")
    env: Optional[Dict[str, Any]] = Field(default=None, description="Environment variables for the server process")
    llm: Optional[BaseLanguageModel] = None
    
    def __init__(self, llm: BaseLanguageModel, **kwargs):
        server_command = kwargs.pop("server_command", "")
        server_args = kwargs.pop("server_args", [])
        env = kwargs.pop("env", None)
        
        super().__init__(llm=llm, **kwargs)
        
        # Set the server parameters
        object.__setattr__(self, "server_command", server_command)
        object.__setattr__(self, "server_args", server_args)
        object.__setattr__(self, "env", env)
        object.__setattr__(self, "exit_stack", AsyncExitStack())
        object.__setattr__(self, "stdio", None)
        object.__setattr__(self, "stdin", None)
        object.__setattr__(self, "session", None)
        object.__setattr__(self, "tools", [])
        object.__setattr__(self, "actions", [])

    def execute(self, server_command: str = None, server_args: List[str] = None, env: dict = None) -> Dict[str, Any]:
        """
        Execute the MCP server connection and tool conversion.
        
        Args:
            server_command (str): The command to start/connect to the MCP server.
            server_args (List[str]): Arguments for the server command.
            env (dict): Environment variables for the server process.
            
        Returns:
            Dict containing the created actions and connection status.
        """
        return asyncio.run(self._execute_async(server_command, server_args, env))
    
    async def execute_async(self, server_command: str = None, server_args: List[str] = None, env: dict = None) -> Dict[str, Any]:
        """
        Async version of execute for use in async contexts.
        
        Args:
            server_command (str): The command to start/connect to the MCP server.
            server_args (List[str]): Arguments for the server command.
            env (dict): Environment variables for the server process.
            
        Returns:
            Dict containing the created actions and connection status.
        """
        return await self._execute_async(server_command, server_args, env)
    
    async def _execute_async(self, server_command: str = None, server_args: List[str] = None, env: dict = None) -> Dict[str, Any]:
        """
        Async implementation of the MCP server connection and tool conversion.
        """
        server_command = server_command or self.server_command
        server_args = server_args or self.server_args
        env = env or self.env
        
        if not server_command:
            return {"status": "error", "error": "server_command is required"}
            
        try:
            server_params = StdioServerParameters(
                command=server_command,
                args=server_args or [],
                env=env,
            )
            stdio_transport = await object.__getattribute__(self, "exit_stack").enter_async_context(stdio_client(server_params))
            object.__setattr__(self, "stdio", stdio_transport[0])
            object.__setattr__(self, "stdin", stdio_transport[1])
            session = await object.__getattribute__(self, "exit_stack").enter_async_context(ClientSession(stdio_transport[0], stdio_transport[1]))
            object.__setattr__(self, "session", session)
            await session.initialize()
            response = await session.list_tools()
            object.__setattr__(self, "tools", response.tools)
            self._create_actions_from_tools()
            
            return {
                "status": "success",
                "actions": object.__getattribute__(self, "actions"),
                "tools_count": len(object.__getattribute__(self, "tools")),
                "actions_count": len(object.__getattribute__(self, "actions"))
            }
        except Exception as e:
            try:
                await object.__getattribute__(self, "exit_stack").aclose()
            except:
                pass
            return {
                "status": "error",
                "error": str(e),
                "actions": [],
                "tools_count": 0,
                "actions_count": 0
            }

    def _create_actions_from_tools(self):
        object.__setattr__(self, "actions", [])
        for tool in self.tools:
            action_cls = self._make_action_class(tool)
            action_instance = action_cls(llm=self.llm, session=object.__getattribute__(self, "session"))
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

    def close(self):
        """Close the MCP connection and clean up resources."""
        asyncio.run(self._close_async())
    
    async def close_async(self):
        """Async version of close for use in async contexts."""
        await self._close_async()
    
    async def _close_async(self):
        """Async implementation of the close method."""
        try:
            await object.__getattribute__(self, "exit_stack").aclose()
        except (asyncio.CancelledError, GeneratorExit):
            print("MCP client cleanup cancelled (suppressed CancelledError/GeneratorExit)")
        except Exception as e:
            print(f"Warning: Error during MCP client cleanup: {e}")
        finally:
            object.__setattr__(self, "session", None) 
            