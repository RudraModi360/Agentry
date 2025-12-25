import json
import asyncio
from typing import List, Dict, Any, Callable, Awaitable, Optional
from datetime import datetime
from agentry.providers.base import LLMProvider
from agentry.tools import ALL_TOOL_SCHEMAS, DANGEROUS_TOOLS, APPROVAL_REQUIRED_TOOLS, execute_tool
try:
    from agentry.mcp_client import MCPClientManager
except ImportError:
    # Fallback if running from different context
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from agentry.mcp_client import MCPClientManager


class ClientSession:
    """Represents a single client conversation session with isolated context."""
    
    def __init__(self, session_id: str, system_message: str):
        self.session_id = session_id
        self.messages: List[Dict[str, Any]] = [{"role": "system", "content": system_message}]
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.metadata: Dict[str, Any] = {}
    
    def update_activity(self):
        """Update the last activity timestamp."""
        self.last_activity = datetime.now()
    
    def add_message(self, message: Dict[str, Any]):
        """Add a message to the session history."""
        self.messages.append(message)
        self.update_activity()
    
    def clear_history(self, keep_system: bool = True):
        """Clear conversation history, optionally keeping system message."""
        if keep_system:
            self.messages = [msg for msg in self.messages if msg.get('role') == 'system']
        else:
            self.messages = []
        self.update_activity()
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of the session context."""
        return {
            "session_id": self.session_id,
            "message_count": len(self.messages),
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "metadata": self.metadata
        }


class MCPAgent:
    """
    Multi-Context Prompting Agent with support for multiple concurrent sessions.
    
    Features:
    - Session management for multiple clients
    - MCP-compatible tool schema generation
    - Enhanced callback system for tool execution
    - Context isolation between sessions
    - Dynamic tool registration and execution
    - Integration with external MCP servers
    """
    
    def __init__(
        self,
        provider: LLMProvider,
        system_message: str = "You are a helpful AI assistant with access to various tools.",
        debug: bool = False,
        max_iterations: int = 20,
        session_timeout: int = 3600,  # 1 hour default
        mcp_client_manager: Optional[MCPClientManager] = None
    ):
        self.provider = provider
        self.default_system_message = system_message
        self.debug = debug
        self.max_iterations = max_iterations
        self.session_timeout = session_timeout
        self.mcp_client_manager = mcp_client_manager
        
        # Session management
        self.sessions: Dict[str, ClientSession] = {}
        
        # Callbacks
        self.on_tool_start: Optional[Callable[[str, str, Dict], None]] = None
        self.on_tool_end: Optional[Callable[[str, str, Any], None]] = None
        self.on_tool_approval: Optional[Callable[[str, str, Dict], Awaitable[bool]]] = None
        self.on_final_message: Optional[Callable[[str, str], None]] = None
        self.on_session_created: Optional[Callable[[str], None]] = None
        self.on_session_destroyed: Optional[Callable[[str], None]] = None
    
    def set_tool_callbacks(
        self,
        on_tool_start: Optional[Callable[[str, str, Dict], None]] = None,
        on_tool_end: Optional[Callable[[str, str, Any], None]] = None,
        on_tool_approval: Optional[Callable[[str, str, Dict], Awaitable[bool]]] = None,
        on_final_message: Optional[Callable[[str, str], None]] = None,
    ):
        """Set callbacks for tool execution events."""
        self.on_tool_start = on_tool_start
        self.on_tool_end = on_tool_end
        self.on_tool_approval = on_tool_approval
        self.on_final_message = on_final_message
    
    def set_session_callbacks(
        self,
        on_session_created: Optional[Callable[[str], None]] = None,
        on_session_destroyed: Optional[Callable[[str], None]] = None,
    ):
        """Set callbacks for session lifecycle events."""
        self.on_session_created = on_session_created
        self.on_session_destroyed = on_session_destroyed
    
    def create_session(
        self, 
        session_id: str, 
        system_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ClientSession:
        """Create a new client session with isolated context."""
        if session_id in self.sessions:
            raise ValueError(f"Session {session_id} already exists")
        
        system_msg = system_message or self.default_system_message
        session = ClientSession(session_id, system_msg)
        
        if metadata:
            session.metadata = metadata
        
        self.sessions[session_id] = session
        
        if self.on_session_created:
            self.on_session_created(session_id)
        
        if self.debug:
            print(f"[MCP] Created session: {session_id}")
        
        return session
    
    def get_session(self, session_id: str) -> Optional[ClientSession]:
        """Get an existing session by ID."""
        return self.sessions.get(session_id)
    
    def destroy_session(self, session_id: str) -> bool:
        """Destroy a session and clean up resources."""
        if session_id not in self.sessions:
            return False
        
        del self.sessions[session_id]
        
        if self.on_session_destroyed:
            self.on_session_destroyed(session_id)
        
        if self.debug:
            print(f"[MCP] Destroyed session: {session_id}")
        
        return True
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions with their summaries."""
        return [session.get_context_summary() for session in self.sessions.values()]
    
    def cleanup_stale_sessions(self) -> int:
        """Remove sessions that have exceeded the timeout period."""
        now = datetime.now()
        stale_sessions = []
        
        for session_id, session in self.sessions.items():
            time_diff = (now - session.last_activity).total_seconds()
            if time_diff > self.session_timeout:
                stale_sessions.append(session_id)
        
        for session_id in stale_sessions:
            self.destroy_session(session_id)
        
        return len(stale_sessions)
    
    async def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get all tools including internal and external MCP tools."""
        tools = list(ALL_TOOL_SCHEMAS)
        
        if self.mcp_client_manager:
            external_tools = await self.mcp_client_manager.get_tools()
            tools.extend(external_tools)
            
        return tools

    async def list_mcp_tools_schema(self) -> List[Dict[str, Any]]:
        """
        Generate MCP-compatible tool schema from registered tools.
        
        Returns:
            List of tool definitions in MCP format with name, description, and input schema.
        """
        mcp_tools = []
        all_tools = await self.get_all_tools()
        
        for tool in all_tools:
            mcp_tool = {
                "name": tool["function"]["name"],
                "description": tool["function"]["description"],
                "input_schema": tool["function"]["parameters"],
                "dangerous": tool["function"]["name"] in DANGEROUS_TOOLS,
                "requires_approval": tool["function"]["name"] in (DANGEROUS_TOOLS + APPROVAL_REQUIRED_TOOLS)
            }
            mcp_tools.append(mcp_tool)
        
        return mcp_tools
    
    async def export_mcp_config(self, filepath: str = "mcp_tools.json"):
        """Export MCP tool configuration to a JSON file."""
        config = {
            "version": "1.0",
            "tools": await self.list_mcp_tools_schema(),
            "metadata": {
                "provider": self.provider.__class__.__name__,
                "max_iterations": self.max_iterations,
                "session_timeout": self.session_timeout
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        
        if self.debug:
            print(f"[MCP] Exported configuration to {filepath}")
    
    async def chat(
        self, 
        user_input: str, 
        session_id: str = "default",
        create_if_missing: bool = True
    ) -> Optional[str]:
        """
        Process a chat message within a specific session context.
        
        Args:
            user_input: The user's message
            session_id: The session identifier
            create_if_missing: Whether to create the session if it doesn't exist
        
        Returns:
            The final assistant response or None if max iterations reached
        """
        # Get or create session
        session = self.get_session(session_id)
        if not session:
            if create_if_missing:
                session = self.create_session(session_id)
            else:
                raise ValueError(f"Session {session_id} does not exist")
        
        # Add user message
        session.add_message({"role": "user", "content": user_input})
        
        # Get all available tools
        all_tools = await self.get_all_tools()
        
        # Agentic loop
        for iteration in range(self.max_iterations):
            if self.debug:
                print(f"[MCP] Session {session_id} - Iteration {iteration + 1}/{self.max_iterations}")
            
            # Get response from provider
            try:
                response_message = await self.provider.chat(session.messages, tools=all_tools)
            except Exception as e:
                error_str = str(e).lower()
                # Check for various forms of empty/invalid response errors
                if "empty" in error_str or ("model output" in error_str and "tool calls" in error_str):
                    if self.debug:
                        print(f"[MCP] Encountered empty response error. Retrying...")
                    
                    # Retry once
                    try:
                        response_message = await self.provider.chat(session.messages, tools=all_tools)
                    except Exception as retry_e:
                        if self.debug:
                            print(f"[MCP] Retry with tools failed: {retry_e}")
                            print(f"[MCP] Attempting fallback without tools...")
                        
                        # Fallback: Try without tools
                        try:
                            response_message = await self.provider.chat(session.messages, tools=None)
                        except Exception as fallback_e:
                            error_msg = "Error: The model returned an invalid response even after fallback. Please try a different model or query."
                            print(f"[MCP] Fallback failed: {fallback_e}")
                            if self.on_final_message:
                                self.on_final_message(session_id, error_msg)
                            return error_msg
                else:
                    error_msg = f"Error: Provider failed with: {str(e)}"
                    print(f"[MCP] Provider error: {e}")
                    if self.on_final_message:
                        self.on_final_message(session_id, error_msg)
                    return error_msg
            
            # Normalize response
            content = None
            tool_calls = None
            
            if isinstance(response_message, dict):  # Ollama style
                content = response_message.get('content')
                tool_calls = response_message.get('tool_calls')
                session.add_message(response_message)
            else:  # Groq/OpenAI object style
                content = response_message.content
                tool_calls = response_message.tool_calls
                
                msg_dict = {"role": "assistant", "content": content}
                if tool_calls:
                    msg_dict["tool_calls"] = [
                        {
                            "id": getattr(tc, 'id', None),
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in tool_calls
                    ]
                session.add_message(msg_dict)
            
            # If no tool calls, return final message
            if not tool_calls:
                if self.on_final_message:
                    self.on_final_message(session_id, content)
                return content
            
            # Process tool calls
            for tool_call in tool_calls:
                # Handle different tool call structures
                if isinstance(tool_call, dict):
                    tool_name = tool_call['function']['name']
                    tool_args = tool_call['function']['arguments']
                    tool_call_id = tool_call.get('id')
                else:
                    tool_name = tool_call.function.name
                    if isinstance(tool_call.function.arguments, str):
                        tool_args = json.loads(tool_call.function.arguments)
                    else:
                        tool_args = tool_call.function.arguments
                    tool_call_id = getattr(tool_call, 'id', None)
                
                # Trigger tool start callback
                if self.on_tool_start:
                    self.on_tool_start(session_id, tool_name, tool_args)
                
                # Check if approval is needed
                needs_approval = tool_name in DANGEROUS_TOOLS or tool_name in APPROVAL_REQUIRED_TOOLS
                
                if needs_approval and self.on_tool_approval:
                    approved = await self.on_tool_approval(session_id, tool_name, tool_args)
                    if not approved:
                        tool_result = {"success": False, "error": "Tool execution denied by user."}
                    else:
                        tool_result = await self._execute_tool_wrapper(tool_name, tool_args)
                else:
                    tool_result = await self._execute_tool_wrapper(tool_name, tool_args)
                
                # Trigger tool end callback
                if self.on_tool_end:
                    self.on_tool_end(session_id, tool_name, tool_result)
                
                # Add tool result to session history
                tool_msg = {
                    "role": "tool",
                    "content": json.dumps(tool_result),
                }
                if tool_call_id:
                    tool_msg["tool_call_id"] = tool_call_id
                else:
                    tool_msg["name"] = tool_name
                    tool_msg["tool_call_name"] = tool_name
                
                session.add_message(tool_msg)
        
        # Max iterations reached
        warning_msg = f"Max iterations ({self.max_iterations}) reached for session {session_id}"
        if self.on_final_message:
            self.on_final_message(session_id, warning_msg)
        
        return None

    async def _execute_tool_wrapper(self, tool_name: str, tool_args: Dict[str, Any]) -> Any:
        """Execute tool, routing to MCP client if needed."""
        # Check if it's an external MCP tool
        if self.mcp_client_manager and tool_name in self.mcp_client_manager.server_tools_map:
            try:
                return await self.mcp_client_manager.execute_tool(tool_name, tool_args)
            except Exception as e:
                return {"success": False, "error": f"External tool execution failed: {e}"}
        
        # Otherwise execute internal tool
        return execute_tool(tool_name, tool_args)

    
    def get_session_history(self, session_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get the full message history for a session."""
        session = self.get_session(session_id)
        return session.messages if session else None
    
    def clear_session_history(self, session_id: str, keep_system: bool = True) -> bool:
        """Clear the conversation history for a session."""
        session = self.get_session(session_id)
        if session:
            session.clear_history(keep_system)
            return True
        return False
