# API Reference: Agent Class

Complete reference for the main `Agent` class.

---

## Class Signature

```python
from logicore import Agent

class Agent:
    def __init__(
        self,
        provider: Union[BaseProvider, str] = None,
        model: str = None,
        system_message: str = None,
        role: str = "general",
        memory: bool = False,
        custom_tools: list = None,
        skills: list = None,
        streaming: bool = True,
        telemetry: bool = False,
        debug: bool = False,
        max_iterations: int = 40,
        temperature: float = 0.7,
        **kwargs
    ) -> None: ...
```

---

## Parameters

### Provider Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `provider` | `BaseProvider \| str` | `None` | LLM provider instance or name ("openai", "groq", "ollama", "gemini", "azure", "anthropic") |
| `model` | `str` | `None` | Model name/ID (e.g., "gpt-4", "llama-3.3-70b"). Auto-detected if None |

### Agent Behavior

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `system_message` | `str` | `None` | Custom system prompt. Auto-generated if None based on role |
| `role` | `str` | `"general"` | Role for behavior ("general", "developer", "analyst", "researcher", "writer") |
| `temperature` | `float` | `0.7` | LLM temperature (0.0-1.0). 0 = deterministic, 1 = creative |

### Tools & Extensions

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `custom_tools` | `list[Callable]` | `None` | List of custom tools to register |
| `skills` | `list[Skill]` | `None` | List of skill packs to load |
| `max_iterations` | `int` | `40` | Max tool-calling loops. Prevents infinite loops |

### Features

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `memory` | `bool` | `False` | Enable persistent memory across sessions |
| `streaming` | `bool` | `True` | Enable real-time token streaming |
| `telemetry` | `bool` | `False` | Enable token counting and usage metrics |
| `debug` | `bool` | `False` | Enable verbose logging for debugging |

---

## Methods

### `chat(message: str) -> str`

Send a message and get response.

```python
agent = Agent()
response = agent.chat("What's the weather?")
print(response)
```

**Parameters:**
- `message` (str): User message

**Returns:**
- `str`: Agent response

**Raises:**
- `ConnectionError`: If provider connection fails
- `ValueError`: If message is empty

---

### `async_chat(message: str) -> str`

Async version of chat. Non-blocking.

```python
import asyncio
agent = Agent()
response = await agent.async_chat("What's the weather?")
```

**Returns:**
- `str`: Agent response

---

### `stream_chat(message: str)`

Stream response token by token.

```python
agent = Agent()
async for chunk in agent.stream_chat("Tell me a story"):
    print(chunk, end="", flush=True)
```

**Yields:**
- `str`: Response chunk

---

### `register_tool(tool: Callable) -> None`

Register a tool after initialization.

```python
@tool
def my_tool(x: str) -> str:
    return f"Result: {x}"

agent = Agent()
agent.register_tool(my_tool)
```

**Parameters:**
- `tool` (Callable): Tool function or class

**Raises:**
- `ValueError`: If tool is invalid

---

### `register_skill(skill: Skill) -> None`

Register a skill pack.

```python
from logicore.skills import DataAnalysisSkill

agent = Agent()
agent.register_skill(DataAnalysisSkill())
```

---

### `get_available_tools() -> list[dict]`

List all available tools.

```python
agent = Agent(custom_tools=[my_tool])
tools = agent.get_available_tools()

for tool in tools:
    print(f"- {tool['name']}: {tool['description']}")
```

**Returns:**
- `list[dict]`: Tool information

---

### Memory Methods

### `memory.search(query: str) -> list[str]`

Search agent's memory.

```python
agent = Agent(memory=True)
agent.chat("My name is Alice")

memories = agent.memory.search("Alice")
print(memories)  # ["My name is Alice"]
```

---

### `memory.clear() -> None`

Clear all memories.

```python
agent = Agent(memory=True)
agent.memory.clear()
```

---

### `memory.export() -> dict`

Export memories.

```python
agent = Agent(memory=True)
agent.chat("My favorite color is blue")

exported = agent.memory.export()
print(exported)  # Dict of all memories
```

---

### Telemetry Methods

### `get_telemetry() -> dict`

Get usage metrics.

```python
agent = Agent(telemetry=True)
agent.chat("Hello")

metrics = agent.get_telemetry()
print(metrics)
# {
#     "tokens_used": 42,
#     "cost_estimate": 0.0021,
#     "latency_ms": 245,
#     "tool_calls": 0
# }
```

---

## Properties

### `provider: BaseProvider`

Current provider.

```python
agent = Agent(provider=GroqProvider())
print(agent.provider)  # GroqProvider instance
```

---

### `model: str`

Current model name.

```python
agent = Agent(model="gpt-4")
print(agent.model)  # "gpt-4"
```

---

### `memory: Memory`

Memory instance.

```python
agent = Agent(memory=True)
print(agent.memory)  # Memory instance
```

---

## Examples

### Basic Chat

```python
from logicore import Agent

agent = Agent()
response = agent.chat("Hello!")
print(response)
```

### With Tools

```python
from logicore import Agent, tool

@tool
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

agent = Agent(custom_tools=[add])
response = agent.chat("What's 5 + 3?")
```

### Multi-Provider

```python
from logicore import Agent
from logicore.providers import GroqProvider

groq = Agent(provider=GroqProvider())
response = groq.chat("Hello!")
```

### With Memory

```python
agent = Agent(memory=True)
agent.chat("My name is Alice")
agent.chat("What's my name?")  # Answers from memory
```

### Production

```python
agent Agent(
    provider="groq",
    memory=True,
    telemetry=True,
    debug=False,
    max_iterations=10
)
response = agent.chat("Important query")
```

---

## Error Handling

### Connection Errors

```python
try:
    agent = Agent(provider="groq")
    response = agent.chat("Hello")
except ConnectionError:
    print("Provider connection failed")
```

### Invalid Tool

```python
try:
    agent.register_tool(invalid_obj)
except ValueError as e:
    print(f"Invalid tool: {e}")
```

---

## Advanced Configuration

### Custom System Prompt

```python
agent = Agent(
    system_message="""
    You are an expert Python developer.
    Your responses are concise and code-focused.
    """
)
```

### Tool Approval

```python
agent = Agent(
    require_approval_for=["delete_file", "execute_shell"]
)
# User must approve before these tools run
```

### Context Compression

```python
agent = Agent(
    context_compression=True,
    max_context_tokens=4000
)
# Long conversations auto-compressed
```

---

## See Also

- [Providers Reference](providers.md)
- [Tools Reference](tools.md)
- [Memory Guide](../concepts/memory.md)
- [Quick Start](../quickstart.md)
