import asyncio
import json
import os
import shutil
from typing import Dict, Any, List, Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult

class MCPClientManager:
    """
    Manages connections to external MCP servers defined in mcp.json.
    Acts as a bridge between the Agent and external MCP tools.
    """
    
    def __init__(self, config_path: str = "mcp.json"):
        self.config_path = config_path
        self.exit_stack = AsyncExitStack()
        self.sessions: Dict[str, ClientSession] = {}
        self.server_tools_map: Dict[str, str] = {}  # tool_name -> server_name
        self.clients: Dict[str, Any] = {} # Keep track of stdio clients
        
    async def load_config(self) -> Dict[str, Any]:
        """Load configuration from mcp.json."""
        if not os.path.exists(self.config_path):
            return {}
            
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[MCP Client] Error loading config: {e}")
            return {}

    async def connect_to_servers(self):
        """Connect to all servers defined in mcp.json."""
        config = await self.load_config()
        servers = config.get("mcpServers", {})
        
        for server_name, server_config in servers.items():
            # Skip if it's the agentry server itself to avoid recursion
            if server_name.startswith("agentry"):
                continue
                
            try:
                command = server_config.get("command")
                args = server_config.get("args", [])
                env = server_config.get("env", {})
                
                # Merge current env with config env
                full_env = os.environ.copy()
                full_env.update(env)
                
                # Resolve command path
                cmd_path = shutil.which(command) or command
                
                server_params = StdioServerParameters(
                    command=cmd_path,
                    args=args,
                    env=full_env
                )
                
                # Connect to server using stdio_client
                client = stdio_client(server_params)
                self.clients[server_name] = client
                read, write = await self.exit_stack.enter_async_context(client)
                
                session = ClientSession(read, write)
                await self.exit_stack.enter_async_context(session)
                
                await session.initialize()
                
                self.sessions[server_name] = session
                print(f"[MCP Client] Connected to server: {server_name}")
                
                # List tools and map them
                result = await session.list_tools()
                for tool in result.tools:
                    self.server_tools_map[tool.name] = server_name
                    
            except Exception as e:
                print(f"[MCP Client] Failed to connect to {server_name}: {e}")

    async def get_tools(self) -> List[Dict[str, Any]]:
        """Get all tools from connected servers in OpenAI/Agentry schema format."""
        all_tools = []
        
        for server_name, session in self.sessions.items():
            try:
                result = await session.list_tools()
                for tool in result.tools:
                    agentry_tool = {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.inputSchema
                        }
                    }
                    all_tools.append(agentry_tool)
            except Exception as e:
                print(f"[MCP Client] Error listing tools from {server_name}: {e}")
                
        return all_tools

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool on the appropriate external server."""
        server_name = self.server_tools_map.get(tool_name)
        if not server_name:
            raise ValueError(f"Tool {tool_name} not found in external servers")
            
        session = self.sessions.get(server_name)
        if not session:
            raise ValueError(f"Session for {server_name} is not active")
            
        result: CallToolResult = await session.call_tool(tool_name, arguments)
        
        # Process result content
        output = []
        if result.content:
            for item in result.content:
                if item.type == "text":
                    output.append(item.text)
                elif item.type == "image":
                    output.append(f"[Image: {item.mimeType}]")
                elif item.type == "resource":
                    output.append(f"[Resource: {item.uri}]")
        
        final_output = "\n".join(output)
        
        if result.isError:
            return {"success": False, "error": final_output}
        else:
            return {"success": True, "content": final_output}

    async def cleanup(self):
        """Close all connections."""
        await self.exit_stack.aclose()
