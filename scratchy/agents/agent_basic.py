"""
BasicAgent - A Generic, Customizable Agent Wrapper

This is the simplest way to create an AI agent with Agentry.
Users can configure their own:
- LLM provider and model
- Custom tools
- Agent name and description
- System prompt

Similar to popular frameworks like LangChain, CrewAI, etc.

Example Usage:
    from scratchy.agents import BasicAgent
    
    # Define custom tools as functions
    def calculator(expression: str) -> str:
        '''Calculate a math expression.'''
        return str(eval(expression))
    
    def get_weather(city: str) -> str:
        '''Get weather for a city.'''
        return f"Weather in {city}: 25°C, Sunny"
    
    # Create agent
    agent = BasicAgent(
        name="MyAssistant",
        description="A helpful assistant that can calculate and check weather",
        provider="ollama",
        model="llama3.2:3b",
        tools=[calculator, get_weather]
    )
    
    # Use it
    response = await agent.chat("What is 15 * 4?")
"""

import asyncio
import inspect
from typing import List, Dict, Any, Optional, Union, Callable
from datetime import datetime
from pydantic import BaseModel, Field, create_model
from scratchy.providers.base import LLMProvider
from scratchy.agents.agent import Agent
from scratchy.tools.base import BaseTool, ToolResult


class BasicAgent:
    """
    A generic, customizable agent wrapper for the Agentry framework.
    
    This is the simplest way to create an AI agent. Just provide:
    - name: Your agent's name
    - description: What your agent does
    - provider: LLM provider (ollama, groq, gemini)
    - model: Model name
    - tools: List of functions or BaseTool instances
    
    The agent will automatically:
    - Convert functions to tools with proper schemas
    - Handle tool execution
    - Manage conversation context
    - Stream responses (if callback provided)
    
    Example:
        agent = BasicAgent(
            name="Calculator",
            description="A math helper",
            tools=[my_calc_function],
            provider="ollama",
            model="llama3.2:3b"
        )
        
        response = await agent.chat("What is 10 + 5?")
    """
    
    def __init__(
        self,
        name: str = "Assistant",
        description: str = "A helpful AI assistant",
        provider: str = "ollama",
        model: str = None,
        api_key: str = None,
        tools: List[Union[Callable, BaseTool]] = None,
        system_prompt: str = None,
        memory_enabled: bool = True,
        debug: bool = False,
        max_iterations: int = 20
    ):
        """
        Create a new BasicAgent.
        
        Args:
            name: Name of the agent (e.g., "ResearchBot", "CodeHelper")
            description: What this agent does (used in system prompt)
            provider: LLM provider - "ollama", "groq", or "gemini"
            model: Model name (provider-specific)
            api_key: API key for cloud providers (groq, gemini)
            tools: List of tools - can be functions or BaseTool instances
            system_prompt: Custom system prompt (optional, auto-generated if not provided)
            memory_enabled: Whether to use memory middleware
            debug: Enable debug logging
            max_iterations: Maximum tool call iterations per chat
        """
        self.name = name
        self.description = description
        self.provider_name = provider
        self.model_name = model
        self.debug = debug
        self.custom_tools = tools or []
        self.custom_system_prompt = system_prompt
        
        # Build system prompt
        if system_prompt:
            self._system_prompt = system_prompt
        else:
            self._system_prompt = self._build_system_prompt()
        
        # Create the underlying agent
        self._agent = Agent(
            llm=provider,
            model=model,
            api_key=api_key,
            system_message=self._system_prompt,
            debug=debug,
            max_iterations=max_iterations
        )
        
        # Register custom tools
        self._register_tools()
        
        # Enable tool support if we have tools
        if self.custom_tools:
            self._agent.supports_tools = True
    
    def _build_system_prompt(self) -> str:
        """Build a Claude-style system prompt based on name and description."""
        tool_descriptions = self._get_tool_descriptions()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"""You are {self.name}, a custom AI assistant built with the Agentry Framework.

<identity>
{self.description}

You are designed to be helpful, efficient, and focused on your specific purpose by leveraging the tools you've been given.
</identity>

<tools>
{tool_descriptions}
</tools>

<guidelines>
1. **Use Your Tools**: When a task matches one of your tools, use it. Don't try to do things manually that tools can do.

2. **Be Direct**: Lead with the answer or action, not preamble. Get to the point.

3. **Be Accurate**: If you're unsure, say so. Don't guess or make up information.

4. **Explain When Helpful**: Briefly explain what you're doing when using tools, but don't over-explain obvious things.

5. **Ask for Clarity**: If a request is ambiguous, ask a focused clarifying question.
</guidelines>

<current_context>
- Current time: {current_time}
- Session: Active
</current_context>

You are ready to help. Use your tools effectively.
"""
    
    def _get_tool_descriptions(self) -> str:
        """Get formatted descriptions of all tools."""
        if not self.custom_tools:
            return "You have no tools available. Respond using your knowledge only."
        
        lines = ["You have access to these tools:"]
        lines.append("")
        
        for tool in self.custom_tools:
            if isinstance(tool, BaseTool):
                lines.append(f"**{tool.name}**")
                lines.append(f"  {tool.description}")
            elif callable(tool):
                name = tool.__name__
                doc = tool.__doc__ or "No description provided"
                lines.append(f"**{name}**")
                lines.append(f"  {doc.strip()}")
            lines.append("")
        
        lines.append("Use tools when they would help accomplish the user's request.")
        return "\n".join(lines)
    
    def _register_tools(self):
        """Register all custom tools with the agent."""
        for tool in self.custom_tools:
            if isinstance(tool, BaseTool):
                # Already a BaseTool - register directly
                self._agent.internal_tools.append(tool.schema)
                self._agent.custom_tool_executors[tool.name] = tool.run
            elif callable(tool):
                # Convert function to tool
                self._register_function_as_tool(tool)
    
    def _register_function_as_tool(self, func: Callable):
        """Convert a Python function to a tool and register it."""
        name = func.__name__
        description = func.__doc__ or f"Execute {name}"
        
        # Get function signature
        sig = inspect.signature(func)
        params = sig.parameters
        
        # Build parameters schema
        properties = {}
        required = []
        
        for param_name, param in params.items():
            # Get type annotation or default to string
            if param.annotation != inspect.Parameter.empty:
                param_type = param.annotation
            else:
                param_type = str
            
            # Map Python types to JSON schema types
            type_mapping = {
                str: "string",
                int: "integer",
                float: "number",
                bool: "boolean",
                list: "array",
                dict: "object",
            }
            json_type = type_mapping.get(param_type, "string")
            
            properties[param_name] = {
                "type": json_type,
                "description": f"Parameter: {param_name}"
            }
            
            # Required if no default value
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
        
        # Create tool schema
        schema = {
            "type": "function",
            "function": {
                "name": name,
                "description": description.strip(),
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }
        
        # Create executor wrapper
        def executor(**kwargs):
            try:
                result = func(**kwargs)
                return ToolResult(success=True, content=str(result))
            except Exception as e:
                return ToolResult(success=False, error=str(e))
        
        # Register with agent
        self._agent.internal_tools.append(schema)
        self._agent.custom_tool_executors[name] = executor
        
        if self.debug:
            print(f"[BasicAgent] Registered tool: {name}")
    
    # --- Public API ---
    
    async def chat(self, message: str, session_id: str = "default") -> str:
        """
        Send a message and get a response.
        
        Args:
            message: The user's message
            session_id: Session ID for conversation context
            
        Returns:
            The agent's response
        """
        return await self._agent.chat(message, session_id=session_id)
    
    def chat_sync(self, message: str, session_id: str = "default") -> str:
        """
        Synchronous version of chat.
        
        Args:
            message: The user's message
            session_id: Session ID for conversation context
            
        Returns:
            The agent's response
        """
        return asyncio.run(self.chat(message, session_id))
    
    def set_callbacks(
        self,
        on_token: Callable[[str], None] = None,
        on_tool_start: Callable[[str, str, dict], None] = None,
        on_tool_end: Callable[[str, str, Any], None] = None,
        on_final_message: Callable[[str, str], None] = None
    ):
        """
        Set callbacks for streaming and tool events.
        
        Args:
            on_token: Called for each streaming token
            on_tool_start: Called when a tool starts (session_id, name, args)
            on_tool_end: Called when a tool ends (session_id, name, result)
            on_final_message: Called when response is complete (session_id, content)
        """
        self._agent.set_callbacks(
            on_token=on_token,
            on_tool_start=on_tool_start,
            on_tool_end=on_tool_end,
            on_final_message=on_final_message
        )
    
    def add_tool(self, tool: Union[Callable, BaseTool]):
        """
        Add a new tool to the agent.
        
        Args:
            tool: A function or BaseTool instance
        """
        self.custom_tools.append(tool)
        if isinstance(tool, BaseTool):
            self._agent.internal_tools.append(tool.schema)
            self._agent.custom_tool_executors[tool.name] = tool.run
        else:
            self._register_function_as_tool(tool)
    
    def add_tools(self, tools: List[Union[Callable, BaseTool]]):
        """Add multiple tools at once."""
        for tool in tools:
            self.add_tool(tool)
    
    def clear_history(self, session_id: str = "default"):
        """Clear conversation history for a session."""
        self._agent.clear_session(session_id)
    
    def get_session(self, session_id: str = "default"):
        """Get conversation session."""
        return self._agent.get_session(session_id)
    
    @property
    def tools(self) -> List[str]:
        """Get list of registered tool names."""
        return [t.get("function", {}).get("name") for t in self._agent.internal_tools]
    
    @property
    def system_prompt(self) -> str:
        """Get the current system prompt."""
        return self._system_prompt
    
    async def cleanup(self):
        """Cleanup resources."""
        await self._agent.cleanup()
    
    def __repr__(self):
        return f"BasicAgent(name='{self.name}', provider='{self.provider_name}', tools={self.tools})"


# --- Convenience Functions ---

def create_agent(
    name: str = "Assistant",
    description: str = "A helpful AI assistant",
    tools: List[Callable] = None,
    provider: str = "ollama",
    model: str = None,
    api_key: str = None,
    **kwargs
) -> BasicAgent:
    """
    Quick way to create a BasicAgent.
    
    Example:
        agent = create_agent(
            name="MathBot",
            description="Helps with math",
            tools=[add, subtract, multiply],
            provider="ollama",
            model="llama3.2:3b"
        )
    """
    return BasicAgent(
        name=name,
        description=description,
        tools=tools,
        provider=provider,
        model=model,
        api_key=api_key,
        **kwargs
    )


def tool(description: str = None):
    """
    Decorator to mark a function as a tool with a description.
    
    Example:
        @tool("Calculate a math expression")
        def calculator(expression: str) -> str:
            return str(eval(expression))
    """
    def decorator(func: Callable) -> Callable:
        if description:
            func.__doc__ = description
        func._is_tool = True
        return func
    return decorator
