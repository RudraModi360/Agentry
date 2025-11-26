import json
import asyncio
from typing import List, Dict, Any, Callable, Awaitable, Optional, Union, get_type_hints
from datetime import datetime
from scratchy.providers.base import LLMProvider
from scratchy.tools import ALL_TOOL_SCHEMAS, DANGEROUS_TOOLS, APPROVAL_REQUIRED_TOOLS, execute_tool
from scratchy.config.prompts import get_system_prompt

try:
    from scratchy.mcp_client import MCPClientManager
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from scratchy.mcp_client import MCPClientManager

class AgentSession:
    """Represents a conversation session."""
    def __init__(self, session_id: str, system_message: str):
        self.session_id = session_id
        self.messages: List[Dict[str, Any]] = [{"role": "system", "content": system_message}]
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.metadata: Dict[str, Any] = {}
    
    def add_message(self, message: Dict[str, Any]):
        self.messages.append(message)
        self.last_activity = datetime.now()
    
    def clear_history(self, keep_system: bool = True):
        if keep_system:
            self.messages = [msg for msg in self.messages if msg.get('role') == 'system']
        else:
            self.messages = []
        self.last_activity = datetime.now()

class Agent:
    """
    A unified, modular AI Agent that supports:
    - Internal tools (filesystem, web, etc.)
    - External MCP tools (Excel, etc.)
    - Multi-session management
    - Custom tool registration
    """
    
    def __init__(
        self,
        llm: Union[LLMProvider, str] = "ollama",
        model: str = None,
        api_key: str = None,
        system_message: str = None,
        role: str = "general",
        debug: bool = False,
        max_iterations: int = 20
    ):
        # Initialize Provider
        if isinstance(llm, str):
            self.provider = self._create_provider(llm, model, api_key)
            model_name = model or "Default Model"
        else:
            self.provider = llm
            model_name = getattr(llm, "model_name", "Custom Provider")

        self.default_system_message = system_message or get_system_prompt(model_name, role)
        self.debug = debug
        self.max_iterations = max_iterations
        
        # Tool Management
        self.internal_tools = []  # List of schemas
        self.mcp_managers: List[MCPClientManager] = []
        self.custom_tool_executors: Dict[str, Callable] = {}
        
        # Session Management
        self.sessions: Dict[str, AgentSession] = {}
        
        # Callbacks
        self.callbacks = {
            "on_tool_start": None,
            "on_tool_end": None,
            "on_tool_approval": None,
            "on_final_message": None
        }

    def _create_provider(self, provider_name: str, model: str, api_key: str) -> LLMProvider:
        """Factory method to create providers from strings."""
        provider_name = provider_name.lower()
        
        if provider_name == "ollama":
            from scratchy.providers.ollama_provider import OllamaProvider
            return OllamaProvider(model_name=model or "gpt-oss:20b-cloud")
            
        elif provider_name == "groq":
            from scratchy.providers.groq_provider import GroqProvider
            return GroqProvider(model_name=model or "llama-3.3-70b-versatile", api_key=api_key)
            
        elif provider_name == "gemini":
            from scratchy.providers.gemini_provider import GeminiProvider
            return GeminiProvider(model_name=model or "gemini-pro", api_key=api_key)
            
        else:
            raise ValueError(f"Unknown provider: {provider_name}. Use 'ollama', 'groq', or 'gemini'.")


    # --- Tool Management ---

    def load_default_tools(self):
        """Load all built-in tools (Filesystem, Web, Execution)."""
        self.internal_tools.extend(ALL_TOOL_SCHEMAS)
        if self.debug:
            print(f"[Agent] Loaded {len(ALL_TOOL_SCHEMAS)} default tools.")

    async def add_mcp_server(self, config_path: str = "mcp.json"):
        """Connect to MCP servers defined in a config file and add their tools."""
        manager = MCPClientManager(config_path)
        await manager.connect_to_servers()
        self.mcp_managers.append(manager)
        if self.debug:
            print(f"[Agent] Added MCP servers from {config_path}")

    def add_custom_tool(self, schema: Dict[str, Any], executor: Callable):
        """Add a single custom tool with its schema and execution function."""
        self.internal_tools.append(schema)
        tool_name = schema.get("function", {}).get("name")
        if tool_name:
            self.custom_tool_executors[tool_name] = executor
            if self.debug:
                print(f"[Agent] Added custom tool: {tool_name}")

    def register_tool_from_function(self, func: Callable):
        """
        Automatically registers a Python function as a tool.
        Generates the schema from the function's signature and docstring.
        """
        import inspect
        
        name = func.__name__
        description = func.__doc__ or "No description provided."
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)
        
        parameters = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self': continue
            
            # Map Python types to JSON types
            py_type = type_hints.get(param_name, str)
            json_type = "string"
            if py_type == int: json_type = "integer"
            elif py_type == float: json_type = "number"
            elif py_type == bool: json_type = "boolean"
            elif py_type == list: json_type = "array"
            elif py_type == dict: json_type = "object"
            
            parameters["properties"][param_name] = {
                "type": json_type,
                "description": f"Parameter {param_name}"
            }
            
            if param.default == inspect.Parameter.empty:
                parameters["required"].append(param_name)
                
        schema = {
            "type": "function",
            "function": {
                "name": name,
                "description": description.strip(),
                "parameters": parameters
            }
        }
        
        self.add_custom_tool(schema, func)

    async def get_all_tools(self) -> List[Dict[str, Any]]:
        """Aggregate all tools (Internal + MCP)."""
        tools = list(self.internal_tools)
        
        for manager in self.mcp_managers:
            mcp_tools = await manager.get_tools()
            tools.extend(mcp_tools)
            
        return tools

    # --- Session Management ---

    def get_session(self, session_id: str = "default") -> AgentSession:
        """Get or create a session."""
        if session_id not in self.sessions:
            self.sessions[session_id] = AgentSession(session_id, self.default_system_message)
        return self.sessions[session_id]

    def clear_session(self, session_id: str = "default"):
        if session_id in self.sessions:
            self.sessions[session_id].clear_history()

    # --- Execution ---

    def set_callbacks(self, **kwargs):
        """Set callbacks: on_tool_start, on_tool_end, on_tool_approval, on_final_message."""
        self.callbacks.update(kwargs)

    async def chat(self, user_input: str, session_id: str = "default") -> str:
        """Main chat loop."""
        session = self.get_session(session_id)
        session.add_message({"role": "user", "content": user_input})
        
        all_tools = await self.get_all_tools()
        
        for i in range(self.max_iterations):
            if self.debug:
                print(f"[Agent] Iteration {i+1}/{self.max_iterations}")
            
            # 1. Get response from LLM
            response = None
            try:
                response = await self.provider.chat(session.messages, tools=all_tools)
            except Exception as e:
                # Error handling & Retry logic
                error_str = str(e).lower()
                # Broaden the check for empty/invalid response errors
                if (
                    "empty" in error_str 
                    or "tool calls" in error_str 
                    or "model output must contain" in error_str
                    or "output text or tool calls" in error_str
                    or "unexpected" in error_str
                ):
                    if self.debug: print(f"[Agent] Response error detected: {error_str}. Retrying...")
                    
                    # First retry with tools
                    try:
                        await asyncio.sleep(1) # Short delay
                        response = await self.provider.chat(session.messages, tools=all_tools)
                    except Exception as retry_error:
                        # Fallback to no tools
                        if self.debug: print(f"[Agent] Retry with tools failed: {retry_error}. Falling back to no tools...")
                        try:
                            await asyncio.sleep(1)
                            response = await self.provider.chat(session.messages, tools=None)
                        except Exception as fallback_error:
                            # Last resort: return friendly error message
                            error_msg = f"I encountered an error from the model: {str(fallback_error)}. Please try again."
                            if self.debug: 
                                print(f"[Agent] All retries failed: {fallback_error}")
                            if self.callbacks["on_final_message"]:
                                self.callbacks["on_final_message"](session_id, error_msg)
                            return error_msg
                else:
                    # Different error, re-raise
                    if self.debug: print(f"[Agent] Unhandled error: {error_str}")
                    raise e
            
            # If we still don't have a response, skip this iteration
            if response is None:
                continue

            # 2. Parse Response
            content = None
            tool_calls = None
            
            if isinstance(response, dict): # Ollama
                content = response.get('content')
                tool_calls = response.get('tool_calls')
                session.add_message(response)
            else: # Object (Groq/Gemini)
                content = response.content
                tool_calls = response.tool_calls
                # Convert to dict for history
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

            # 3. Handle Final Response
            if not tool_calls:
                if self.callbacks["on_final_message"]:
                    self.callbacks["on_final_message"](session_id, content)
                return content

            # 4. Execute Tools
            for tc in tool_calls:
                # Extract details
                if isinstance(tc, dict):
                    name = tc['function']['name']
                    args = tc['function']['arguments']
                    tc_id = tc.get('id')
                else:
                    name = tc.function.name
                    args = tc.function.arguments
                    if isinstance(args, str): args = json.loads(args)
                    tc_id = getattr(tc, 'id', None)

                if self.callbacks["on_tool_start"]:
                    self.callbacks["on_tool_start"](session_id, name, args)

                # Approval
                approved = True
                if self._requires_approval(name):
                    if self.callbacks["on_tool_approval"]:
                        approved = await self.callbacks["on_tool_approval"](session_id, name, args)
                    else:
                        # If no callback is set but approval is required, we pass (backward compatibility)
                        pass

                if not approved:
                    result = {"error": "Denied by user"}
                else:
                    result = await self._execute_tool(name, args)

                if self.callbacks["on_tool_end"]:
                    self.callbacks["on_tool_end"](session_id, name, result)

                # Add result to history
                tool_msg = {
                    "role": "tool",
                    "content": json.dumps(result)
                }
                if tc_id: tool_msg["tool_call_id"] = tc_id
                else: tool_msg["name"] = name
                
                session.add_message(tool_msg)

        return "Max iterations reached."

    def _requires_approval(self, name: str) -> bool:
        """Check if a tool requires user approval."""
        # 1. Check explicit lists
        if name in DANGEROUS_TOOLS or name in APPROVAL_REQUIRED_TOOLS:
            return True
        
        # 2. Check MCP and Custom tools
        is_mcp = any(name in m.server_tools_map for m in self.mcp_managers)
        is_custom = name in self.custom_tool_executors
        
        if is_mcp or is_custom:
            # Heuristic for critical operations
            # We check if the name implies any state-changing or external side-effect
            critical_keywords = [
                'write', 'edit', 'update', 'delete', 'create', 'insert', 'modify', 
                'set_', 'execute', 'run', 'upload', 'send', 'post', 'put', 'patch',
                'remove', 'drop', 'alter', 'grant', 'revoke', 'commit'
            ]
            if any(k in name.lower() for k in critical_keywords):
                return True
                
        return False

    async def _execute_tool(self, name: str, args: Dict) -> Any:
        # 1. Custom Tools
        if name in self.custom_tool_executors:
            return self.custom_tool_executors[name](**args)
        
        # 2. MCP Tools
        for manager in self.mcp_managers:
            if name in manager.server_tools_map:
                try:
                    return await manager.execute_tool(name, args)
                except Exception as e:
                    return {"error": str(e)}

        # 3. Internal Default Tools
        return execute_tool(name, args)

    async def cleanup(self):
        for manager in self.mcp_managers:
            await manager.cleanup()
