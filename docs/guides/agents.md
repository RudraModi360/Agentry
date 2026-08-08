---
title: Agents Guide
description: Understanding agent types, configuration, and capabilities
---

# Agents Guide

Agents are the core orchestrators in Logicore. This guide covers agent types, configuration, and best practices.

## Agent Types

### Base Agent

The foundation class with full customization control.

```python
from logicore import Agent

agent = Agent(
    provider="ollama",
    model="qwen3.5:0.8b",
    role="Assistant",
    system_prompt="You are a helpful assistant.",
    tools=["smart"],
    max_iterations=40,
    debug=False,
    telemetry=False
)
```

### SmartAgent

Optimized for reasoning tasks with auto-configuration.

```python
from logicore import SmartAgent

agent = SmartAgent(
    provider="ollama",
    model="qwen3.5:0.8b"
)

# Use the reason() method for step-by-step problem solving
response = await agent.reason("How do I sort a list in Python?")
```

**Features:**
- Auto-configured tool preset
- Built-in reasoning prompts
- Step-by-step problem solving

### CopilotAgent

Coding-focused agent with development tools.

```python
from logicore import CopilotAgent

agent = CopilotAgent(
    provider="openai",
    model="gpt-4o"
)

# Coding-specific methods
explanation = await agent.explain_code("def fib(n): return n if n<2 else fib(n-1)+fib(n-2)")
review = await agent.review_file("main.py")
fix = await agent.fix_bug("IndexError in line 42")
```

**Features:**
- Code explanation
- File review
- Bug fixing
- Code writing

### MCPAgent

Extended tools via Model Context Protocol servers.

```python
from logicore import MCPAgent

agent = MCPAgent(
    provider="ollama",
    model="qwen3.5:0.8b",
    mcp_config_path="mcp.json"
)

# Automatically connects to MCP servers
tools = await agent.get_all_tools()
```

**Features:**
- Deferred tool loading
- Server connection management
- Tool search and filtering

## Configuration Parameters

### Provider Settings

```python
agent = Agent(
    provider="ollama",          # Provider name or instance
    model="qwen3.5:0.8b",      # Model identifier
    api_key="...",              # API key (for cloud providers)
    endpoint="...",             # Custom endpoint URL
)
```

### Behavior Settings

```python
agent = Agent(
    role="Assistant",           # Agent persona
    system_prompt="...",        # Custom system prompt
    reasoning_level="medium",   # low, medium, high
    plan_mode=False,            # Enable plan mode
    max_iterations=40,          # Max tool-call loops
)
```

### Tool Settings

```python
agent = Agent(
    tools=["smart"],            # Tool preset or list
    tool_preset="smart",        # Preset name
    allow_tools={"read_file"},  # Pre-approved tools
    approval_timeout=120.0,     # Seconds to wait for approval
)
```

### Memory Settings

```python
agent = Agent(
    memory=True,                # Enable persistent memory
    memory_dir="~/.logicore/memory",  # Memory storage path
)
```

### Debug Settings

```python
agent = Agent(
    debug=True,                 # Enable debug logging
    telemetry=True,             # Enable telemetry
    agent_id="my-agent",       # Custom agent identifier
)
```

## Tool Presets

| Preset | Tools | Use Case |
|--------|-------|----------|
| `lightweight` | ~16 | Basic filesystem + web |
| `smart` | ~30 | Full agentic toolkit |
| `copilot` | ~18 | Code-focused |
| `full` | All | Maximum capabilities |
| `minimal` | 6 | Basic I/O only |
| `webdev` | ~12 | Web development |

```python
# Using presets
agent = Agent(tools="smart")

# Custom tool list
agent = Agent(tools=["read_file", "write_file", "search_web"])

# Disable all tools
agent = Agent(tools=[])
```

## Session Management

### Creating Sessions

```python
# Implicit session creation
response = await agent.chat("Hello", session_id="my-session")

# Explicit session creation
session = agent.create_session(
    session_id="my-session",
    tags={"project": "demo"}
)
```

### Managing Sessions

```python
# List sessions
sessions = await agent.list_sessions()

# Get session
session = await agent.get_session("my-session")

# Clear session history
await agent.clear_session("my-session")

# Delete session
await agent.delete_session("my-session")
```

### Session Persistence

```python
from logicore.storage import StorageManager

# Create storage backend
storage = StorageManager(
    db_url="sqlite:///sessions.db",
    media_dir="./media"
)

# Attach to agent
agent = Agent(
    provider="ollama",
    storage=storage
)

# Sessions are now persisted
```

## Streaming

### Real-time Token Streaming

```python
async def on_token(token):
    print(token, end="", flush=True)

response = await agent.chat(
    "Tell me a story",
    callbacks={"on_token": on_token},
    stream=True
)
```

### Async Generator Streaming

```python
async for event in agent.stream("Tell me a story"):
    if event.type == "token":
        print(event.content, end="", flush=True)
    elif event.type == "tool_call":
        print(f"\nUsing tool: {event.tool_name}")
```

### Sync Streaming

```python
# For non-async contexts
for event in agent.stream_sync("Tell me a story"):
    print(event.content, end="", flush=True)
```

## Custom Tools

### From Functions

```python
def search_database(query: str, limit: int = 10) -> str:
    """Search the database for records.
    
    Args:
        query: Search query string
        limit: Maximum results to return
    
    Returns:
        JSON string of matching records
    """
    # Your implementation
    return json.dumps(results)

agent = Agent(tools=[search_database])
```

### From Classes

```python
from logicore.tools import BaseTool, ToolResult

class DatabaseTool(BaseTool):
    name = "query_database"
    description = "Execute SQL queries"
    
    def __init__(self, connection):
        self.connection = connection
    
    async def run(self, query: str) -> ToolResult:
        result = self.connection.execute(query)
        return ToolResult(success=True, content=str(result))
    
    def is_read_only(self) -> bool:
        return "SELECT" in query.upper()

agent.add_custom_tool(DatabaseTool(db_connection))
```

### Auto-Registration

```python
# From function (auto-generates schema)
agent.register_tool_from_function(my_function)

# From class
agent.add_custom_tool(MyTool())
```

## Skills

### Loading Skills

```python
# Load single skill
agent.load_skill("excel_operations")

# Load multiple skills
agent.load_skills(["excel_operations", "pdf_operations"])

# Load from index
agent.load_skill_from_index("excel")
```

### Managing Skills

```python
# List available skills
skills = agent.list_available_skills()

# Enable/disable
agent.disable_skill("excel_operations")
agent.enable_skill("excel_operations")

# Unload
agent.unload_skill("excel_operations")
```

## Error Handling

### Tool Errors

```python
try:
    response = await agent.chat("Delete all files")
except ToolExecutionError as e:
    print(f"Tool error: {e}")
except ApprovalTimeoutError:
    print("User denied the operation")
```

### Provider Errors

```python
from logicore.providers import ModelAvailabilityService

availability = ModelAvailabilityService()
availability.register_provider("openai", OpenAIProvider(model="gpt-4o"), priority=1)
availability.register_provider("groq", GroqProvider(model="llama-3.3-70b"), priority=2)

# Automatic failover on provider failure
```

## Best Practices

1. **Use Tool Presets**: Start with `smart` or `copilot` presets
2. **Session IDs**: Use meaningful session IDs for persistence
3. **Error Handling**: Always handle tool approval timeouts
4. **Streaming**: Use streaming for better UX
5. **Memory**: Enable memory for multi-session contexts
6. **Debug Mode**: Enable during development, disable in production

## Next Steps

- [Tools Guide](./tools.md) - Deep dive into tool creation
- [Skills Guide](./skills.md) - Build skill packages
- [Memory Guide](./memory.md) - Persistent context
- [Streaming Guide](./streaming.md) - Real-time responses
- [Architecture](./architecture.md) - System design
