import json
import inspect
import asyncio
from typing import List, Dict, Any, Callable, Awaitable, Optional, Union, get_type_hints
from datetime import datetime
from scratchy.providers.base import LLMProvider
from scratchy.tools import ALL_TOOL_SCHEMAS, DANGEROUS_TOOLS, APPROVAL_REQUIRED_TOOLS, SAFE_TOOLS, execute_tool
from scratchy.config.prompts import get_system_prompt

import sys
import os
from scratchy.mcp_client import MCPClientManager
# from scratchy.user_profile_manager import UserProfileManager
from scratchy.memory.storage import PersistentMemoryStore
from scratchy.memory.middleware import MemoryMiddleware
from scratchy.memory.vfs import VirtualFileSystem

class AgentSession:
    """Represents a conversation session."""
    def __init__(self, session_id: str, system_message: str):
        self.session_id = session_id
        self.messages: List[Dict[str, Any]] = [{"role": "system", "content": system_message}]
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.metadata: Dict[str, Any] = {}
        self.files: Dict[str, str] = {} # VFS: Filename -> Content
    
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
    - Persistent Memory Middleware
    """
    
    def __init__(
        self,
        llm: Union[LLMProvider, str] = "ollama",
        model: str = None,
        api_key: str = None,
        system_message: str = None,
        role: str = "general",
        debug: bool = False,
        max_iterations: int = 40
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
        
        # Memory Middleware
        self.memory_store = PersistentMemoryStore() # Default to sqlite in user_data
        self.memory_middleware = MemoryMiddleware(self.provider, self.memory_store)
        
        # Context Middleware (Token Management)
        from scratchy.memory.context_middleware import ContextMiddleware
        self.context_middleware = ContextMiddleware(self.provider, token_threshold=100000)
        
        # Virtual File System
        self.vfs = VirtualFileSystem(self.memory_store)
        
        # Tool support flag - set when load_default_tools is called
        self.supports_tools = False
        self.tools_disabled_reason = None  # Optional message explaining why tools are disabled
        
        # Callbacks
        self.callbacks = {
            "on_tool_start": None,
            "on_tool_end": None,
            "on_tool_approval": None,
            "on_final_message": None,
            "on_token": None  # For streaming token updates
        }

        # Initialize UserProfileManager
        # Removed in favor of MemoryMiddleware
        # profile_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "user_data", "user_profile.md")
        # self.user_profile_manager = UserProfileManager(profile_path, self.provider)

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
        self.internal_tools.extend(self.vfs.get_tool_schemas())
        self.supports_tools = True  # Mark that tools are loaded and supported
        if self.debug:
            print(f"[Agent] Loaded {len(ALL_TOOL_SCHEMAS)} default tools + VFS tools.")
    
    def disable_tools(self, reason: str = None):
        """Disable tool support for this agent."""
        self.supports_tools = False
        self.internal_tools = []
        self.tools_disabled_reason = reason or "Tools disabled"
        if self.debug:
            print(f"[Agent] Tools disabled: {self.tools_disabled_reason}")

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
            # Ensure session exists in persistent memory store
            self.memory_store.create_session(session_id)
            
            # Load VFS files
            self.sessions[session_id].files = self.vfs.load_session_files(session_id)
                
        return self.sessions[session_id]

    def clear_session(self, session_id: str = "default"):
        if session_id in self.sessions:
            self.sessions[session_id].clear_history()

    # --- Execution ---

    def set_callbacks(self, **kwargs):
        """Set callbacks: on_tool_start, on_tool_end, on_tool_approval, on_final_message, on_token."""
        self.callbacks.update(kwargs)

    async def chat(self, user_input: Union[str, List[Dict[str, Any]]], session_id: str = "default") -> str:
        """Main chat loop."""
        from scratchy.providers.utils import extract_content

        session = self.get_session(session_id)
        
        # --- Context Management (Middleware) ---
        # Check token limit and summarize if necessary
        session.messages = await self.context_middleware.manage_context(session.messages)

        # --- Handle Multimodal Input ---
        text_for_memory = user_input
        if isinstance(user_input, list):
            text_for_memory, _ = extract_content(user_input)

        # --- Memory Middleware: Process User Input ---
        # Extract insights and retrieve relevant memories
        if self.debug: print(f"[Agent] Middleware: Processing user input for memory...")
        relevant_memories = await self.memory_middleware.process_user_input(session_id, text_for_memory)
        
        # Format memories for injection
        memory_context = ""
        if relevant_memories:
            memory_context = "\n\n=== Relevant Memories ===\n"
            for mem in relevant_memories:
                memory_context += f"- [{mem['type']}] {mem['content']}\n"

        # Inject Memories into System Message
        
        # Construct dynamic system message
        base_system = self.default_system_message
        full_system_msg = base_system
        
        if memory_context:
            full_system_msg += memory_context
            
        # Update system message in history
        if session.messages and session.messages[0]['role'] == 'system':
            session.messages[0]['content'] = full_system_msg
        else:
            session.messages.insert(0, {"role": "system", "content": full_system_msg})

        # Note: We NO LONGER update profile on every turn to reduce latency/overhead.
        # We only update on truncation (above) or explicit session end.

        session.add_message({"role": "user", "content": user_input})
        
        # Only get tools if they're supported
        all_tools = None
        if self.supports_tools:
            all_tools = await self.get_all_tools()
            if self.debug and all_tools:
                print(f"[Agent] Using {len(all_tools)} tools")
        else:
            if self.debug:
                print(f"[Agent] Tool-free mode: {self.tools_disabled_reason or 'Model does not support tools'}")
        # Ensure we have a robust error handling strategy around provider calls
        # This will catch JSON serialization errors and internal server errors
        # and allow the chat session to continue.
        # We’ll wrap the main iteration loop in a try/except block.
        # The errors are logged via simple print statements for visibility.
        # If an error occurs, we’ll return an informative message instead of crashing.

        
        for i in range(self.max_iterations):
            if self.debug:
                print(f"[Agent] Iteration {i+1}/{self.max_iterations}")
            
            # 1. Get response from LLM
            response = None
            try:
                # Use streaming if on_token callback is set and provider supports it
                on_token = self.callbacks.get("on_token")
                if on_token and hasattr(self.provider, 'chat_stream'):
                    response = await self.provider.chat_stream(session.messages, tools=all_tools, on_token=on_token)
                else:
                    response = await self.provider.chat(session.messages, tools=all_tools)
            except Exception as e:
                # Error handling & Retry logic
                error_str = str(e).lower()
                
                # Broaden the check for empty/invalid response errors and now Internal Server Errors
                if (
                    "empty" in error_str 
                    or "tool calls" in error_str 
                    or "model output must contain" in error_str
                    or "output text or tool calls" in error_str
                    or "unexpected" in error_str
                    or "does not support tools" in error_str
                    or "internal server error" in error_str
                    or "status code: -1" in error_str
                    or "status code: 500" in error_str
                ):
                    if self.debug or "internal server error" in error_str: 
                        print(f"[Agent] ⚠️  Response/Provider error: {error_str}. Retrying...")
                    
                    # Retry loop with tools
                    retry_success = False
                    for attempt in range(3):
                        try:
                            if self.debug: print(f"[Agent] Retry attempt {attempt+1} with tools...")
                            await asyncio.sleep(1) # Short delay
                            response = await self.provider.chat(session.messages, tools=all_tools)
                            retry_success = True
                            break
                        except Exception as retry_error:
                            retry_error_str = str(retry_error).lower()
                            if "does not support tools" in retry_error_str:
                                if self.debug: print(f"[Agent] Model doesn't support tools. Aborting tool retries.")
                                break # Stop retrying with tools immediately
                            
                            if self.debug: print(f"[Agent] Retry {attempt+1} failed: {retry_error}")
                    
                    if not retry_success:
                        # Fallback to no tools as a last resort
                        if self.debug: print(f"[Agent] Falling back to no tools...")
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
                    # Different error
                    print(f"\n[Agent] ⚠️  Runtime Error: {e}")
                    # Don't crash, just break or continue?
                    # User asked to continue session chat.
                    # We will return the error as a message to the user so they know something happened.
                    return f"Error during execution: {str(e)}"
            
            # If we still don't have a response, skip this iteration
            if response is None:
                continue

            # 2. Parse Response
            try:
                content = None
                tool_calls = None
                
                if isinstance(response, dict): # Ollama
                    content = response.get('content')
                    tool_calls = response.get('tool_calls')
                    
                    # Sanitize Ollama tool calls to ensure they are dicts
                    if tool_calls:
                         serialized_tool_calls = []
                         for tc in tool_calls:
                             if hasattr(tc, 'dict'): serialized_tool_calls.append(tc.dict())
                             elif hasattr(tc, 'model_dump'): serialized_tool_calls.append(tc.model_dump())
                             elif isinstance(tc, dict): serialized_tool_calls.append(tc)
                             else: 
                                 # Fallback: Try to force serialization or skip
                                 try:
                                     json.dumps(tc)
                                     serialized_tool_calls.append(tc)
                                 except:
                                     if self.debug: print(f"[Agent] ⚠️ Skipping non-serializable tool call: {tc}")
                                     pass
                         response['tool_calls'] = serialized_tool_calls
                         
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
            except Exception as parse_error:
                print(f"[Agent] ⚠️  Response Parsing Error (Ignored): {parse_error}")
                # We can try to recover by adding a text message only
                try:
                     content_safe = getattr(response, 'content', str(response))
                     session.add_message({"role": "assistant", "content": f"(Recovered) {content_safe}"})
                except: pass
                continue

            # 3. Handle Final Response
            if not tool_calls:
                # --- Memory Middleware: Process Agent Output ---
                if self.debug: print(f"[Agent] Middleware: Processing agent output for memory...")
                # We use create_task to not block the response, or await if we want to ensure it's saved?
                # The user wants it "added to memory", implying it's part of the flow.
                # Awaiting ensures it's saved before the next turn.
                await self.memory_middleware.process_agent_output(session_id, content)

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
                    callback = self.callbacks["on_tool_start"]
                    if inspect.iscoroutinefunction(callback):
                        await callback(session_id, name, args)
                    else:
                        callback(session_id, name, args)

                # Approval
                approved = True
                if self._requires_approval(name):
                    if self.callbacks["on_tool_approval"]:
                        approval_result = await self.callbacks["on_tool_approval"](session_id, name, args)
                        
                        if isinstance(approval_result, dict):
                            # User modified arguments
                            args = approval_result
                            approved = True
                        else:
                            # Boolean or None
                            approved = bool(approval_result)
                    else:
                        # If no callback is set but approval is required, we pass (backward compatibility)
                        pass

                if not approved:
                    result = {"error": "Denied by user"}
                else:
                    result = await self._execute_tool(name, args, session_id)

                if self.callbacks["on_tool_end"]:
                    callback = self.callbacks["on_tool_end"]
                    if inspect.iscoroutinefunction(callback):
                        await callback(session_id, name, result)
                    else:
                        callback(session_id, name, result)


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
        # 1. Allow Safe Tools Explicitly
        if name in SAFE_TOOLS:
            return False
            
        # VFS tools are internal memory operations, so they are safe
        if name in ["write_virtual_file", "read_virtual_file", "list_virtual_files"]:
            return False
            
        # Exempt 'computer' tool calls from approval (Claude Computer Use)
        if name == 'computer':
            return False

        # 2. Everything else requires approval
        # This covers DANGEROUS_TOOLS, APPROVAL_REQUIRED_TOOLS, and any unknown MCP/Custom tools
        return True

    async def _execute_tool(self, name: str, args: Dict, session_id: str) -> Any:
        # 0. VFS Tools
        if name in ["write_virtual_file", "read_virtual_file", "list_virtual_files"]:
            session = self.get_session(session_id)
            return self.vfs.execute_tool(session.files, session_id, name, args)

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

