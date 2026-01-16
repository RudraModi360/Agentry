---
layout: page
title: API Reference
nav_order: 4
description: "Complete API documentation for Agentry classes and methods"
---

# API Reference

Complete API documentation for the Agentry framework.

## Table of Contents

1. [Agent Class](#agent-class)
2. [CopilotAgent Class](#copilotagent-class)
3. [SessionManager Class](#sessionmanager-class)
4. [AgentSession Class](#agentsession-class)
5. [Providers](#providers)
6. [Built-in Tools](#built-in-tools)
7. [Type Definitions](#type-definitions)

---

## Agent Class

The main agent class that manages LLM interactions, tool execution, and session handling.

### Constructor

```python
Agent(
    llm: Union[LLMProvider, str] = "ollama",
    model: str = None,
    api_key: str = None,
    endpoint: str = None,
    system_message: str = None,
    role: str = "general",
    debug: bool = False,
    max_iterations: int = 20
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|:----------|:-----|:--------|:------------|
| `llm` | str or LLMProvider | "ollama" | Provider name or instance |
| `model` | str | None | Model name (provider-specific) |
| `api_key` | str | None | API key for cloud providers |
| `endpoint` | str | None | Endpoint URL (for Azure) |
| `system_message` | str | None | Custom system prompt |
| `role` | str | "general" | Agent role: "general" or "engineer" |
| `debug` | bool | False | Enable debug logging |
| `max_iterations` | int | 20 | Maximum tool execution iterations |

**Example:**

```python
from agentry import Agent

agent = Agent(
    llm="groq",
    model="llama-3.3-70b-versatile",
    api_key="your-api-key",
    debug=True
)
```

---

### Methods

#### load_default_tools()

Loads all built-in tools (filesystem, web, execution).

```python
agent.load_default_tools()
```

**Returns:** None

---

#### register_tool_from_function(func)

Registers a Python function as a tool. Automatically generates the schema from function signature and docstring.

```python
def calculate_bmi(weight_kg: float, height_m: float) -> str:
    """Calculate BMI given weight in kg and height in meters."""
    bmi = weight_kg / (height_m ** 2)
    return f"BMI: {bmi:.2f}"

agent.register_tool_from_function(calculate_bmi)
```

**Parameters:**

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `func` | Callable | Python function with type hints and docstring |

**Returns:** None

---

#### add_custom_tool(schema, executor)

Adds a custom tool with a manually defined schema.

```python
schema = {
    "type": "function",
    "function": {
        "name": "my_tool",
        "description": "My custom tool description",
        "parameters": {
            "type": "object",
            "properties": {
                "param": {"type": "string", "description": "Parameter description"}
            },
            "required": ["param"]
        }
    }
}

agent.add_custom_tool(schema, my_executor_function)
```

**Parameters:**

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `schema` | dict | Tool schema in OpenAI function format |
| `executor` | Callable | Function to execute when tool is called |

**Returns:** None

---

#### async add_mcp_server(config_path)

Connects to MCP servers defined in a configuration file.

```python
await agent.add_mcp_server("mcp.json")
```

**Parameters:**

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `config_path` | str | Path to MCP configuration JSON file |

**Returns:** None

---

#### async chat(user_input, session_id)

Main chat interface. Sends a message and returns the agent's response.

```python
response = await agent.chat("Hello!", session_id="user_123")
print(response)
```

**Parameters:**

| Parameter | Type | Default | Description |
|:----------|:-----|:--------|:------------|
| `user_input` | str | Required | User message |
| `session_id` | str | "default" | Session identifier |

**Returns:** str - The agent's response

---

#### get_session(session_id)

Gets or creates a session.

```python
session = agent.get_session("user_123")
print(f"Messages: {len(session.messages)}")
```

**Parameters:**

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `session_id` | str | Session identifier |

**Returns:** AgentSession

---

#### clear_session(session_id)

Clears the session history.

```python
agent.clear_session("user_123")
```

**Parameters:**

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `session_id` | str | Session identifier |

**Returns:** None

---

#### set_callbacks(**kwargs)

Sets event callbacks for tool execution and messages.

```python
def on_tool_start(session_id, name, args):
    print(f"Executing: {name}")

def on_tool_end(session_id, name, result):
    print(f"Result: {result}")

async def on_tool_approval(session_id, name, args):
    return input(f"Approve {name}? (y/n): ").lower() == 'y'

def on_final_message(session_id, content):
    print(f"Response: {content}")

agent.set_callbacks(
    on_tool_start=on_tool_start,
    on_tool_end=on_tool_end,
    on_tool_approval=on_tool_approval,
    on_final_message=on_final_message
)
```

**Available Callbacks:**

| Callback | Signature | Description |
|:---------|:----------|:------------|
| `on_tool_start` | `(session_id, name, args)` | Called before tool execution |
| `on_tool_end` | `(session_id, name, result)` | Called after tool execution |
| `on_tool_approval` | `async (session_id, name, args) -> bool` | Called for dangerous tools |
| `on_final_message` | `(session_id, content)` | Called with final response |

**Returns:** None

---

#### async cleanup()

Cleans up resources (closes MCP connections).

```python
await agent.cleanup()
```

**Returns:** None

---

## CopilotAgent Class

Specialized agent for coding tasks. Inherits from `Agent`.

### Constructor

```python
CopilotAgent(
    llm: Union[LLMProvider, str] = "ollama",
    model: str = None,
    api_key: str = None,
    system_message: str = None,
    debug: bool = False
)
```

The CopilotAgent automatically:
- Uses the "engineer" role for coding-focused prompts
- Loads default tools

---

### Additional Methods

#### async explain_code(code)

Explains a code snippet.

```python
explanation = await copilot.explain_code("""
def factorial(n):
    return 1 if n <= 1 else n * factorial(n-1)
""")
```

**Returns:** str - Explanation of the code

---

#### async review_file(filepath)

Reviews a file for bugs and improvements.

```python
review = await copilot.review_file("my_script.py")
```

**Returns:** str - Code review feedback

---

#### async general_chat(user_input)

Switches to general assistant mode (uses a separate session).

```python
response = await copilot.general_chat("Tell me a joke")
```

**Returns:** str - Response in general context

---

## SessionManager Class

Manages session persistence with `.toon` format.

### Constructor

```python
SessionManager(history_dir: str = None)
```

**Parameters:**

| Parameter | Type | Default | Description |
|:----------|:-----|:--------|:------------|
| `history_dir` | str | None | Directory for session files (default: `agentry/session_history/`) |

---

### Methods

#### save_session(session_id, messages)

Saves session to a `.toon` file.

```python
sm = SessionManager()
sm.save_session("my_session", session.messages)
```

**Returns:** None

---

#### load_session(session_id)

Loads session from a `.toon` file.

```python
messages = sm.load_session("my_session")
```

**Returns:** Optional[List[Dict]] - Message list or None

---

#### list_sessions()

Lists all saved sessions.

```python
sessions = sm.list_sessions()
for s in sessions:
    print(f"{s['id']}: {s['message_count']} messages")
```

**Returns:** List[Dict] with keys: `id`, `created_at`, `message_count`

---

#### delete_session(session_id)

Deletes a session file.

```python
sm.delete_session("old_session")
```

**Returns:** bool - True if deleted, False if not found

---

#### session_exists(session_id)

Checks if a session exists.

```python
if sm.session_exists("my_session"):
    print("Session found")
```

**Returns:** bool

---

## AgentSession Class

Represents a conversation session.

### Attributes

| Attribute | Type | Description |
|:----------|:-----|:------------|
| `session_id` | str | Unique identifier |
| `messages` | List[Dict] | Message history |
| `created_at` | datetime | Creation timestamp |
| `last_activity` | datetime | Last activity timestamp |
| `metadata` | Dict | Custom metadata |

---

### Methods

#### add_message(message)

Adds a message to the session.

```python
session.add_message({"role": "user", "content": "Hello"})
```

---

#### clear_history(keep_system)

Clears message history.

```python
session.clear_history(keep_system=True)
```

**Parameters:**

| Parameter | Type | Default | Description |
|:----------|:-----|:--------|:------------|
| `keep_system` | bool | True | Whether to keep system message |

---

## Providers

### OllamaProvider

```python
from agentry.providers import OllamaProvider

provider = OllamaProvider(
    model="llama3.2",
    host="http://localhost:11434"
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|:----------|:-----|:--------|:------------|
| `model` | str | Required | Model name |
| `host` | str | "http://localhost:11434" | Ollama server URL |

---

### GroqProvider

```python
from agentry.providers import GroqProvider

provider = GroqProvider(
    model="llama-3.3-70b-versatile",
    api_key="your-api-key"
)
```

**Parameters:**

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `model` | str | Model name |
| `api_key` | str | Groq API key |

---

### GeminiProvider

```python
from agentry.providers import GeminiProvider

provider = GeminiProvider(
    model="gemini-2.0-flash",
    api_key="your-api-key"
)
```

**Parameters:**

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `model` | str | Model name |
| `api_key` | str | Google API key |

---

### AzureProvider

```python
from agentry.providers import AzureProvider

provider = AzureProvider(
    model="gpt-4",
    api_key="your-api-key",
    endpoint="https://your-resource.openai.azure.com"
)
```

**Parameters:**

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `model` | str | Deployment name |
| `api_key` | str | Azure API key |
| `endpoint` | str | Azure OpenAI endpoint URL |

---

## Built-in Tools

### Filesystem Tools

| Tool | Description |
|:-----|:------------|
| `read_file` | Read file contents |
| `create_file` | Create new files |
| `edit_file` | Modify existing files |
| `delete_file` | Remove files |
| `list_directory` | Browse directories |
| `search_files` | Find text in files |
| `fast_grep` | Quick keyword search |

### Execution Tools

| Tool | Description |
|:-----|:------------|
| `run_shell_command` | Execute shell commands |
| `execute_python` | Execute Python code |

### Web Tools

| Tool | Description |
|:-----|:------------|
| `web_search` | Search the web |
| `fetch_url` | Fetch URL content |

### Git Tools

| Tool | Description |
|:-----|:------------|
| `git_command` | Execute Git operations |

### Document Tools

| Tool | Description |
|:-----|:------------|
| `pandoc_convert` | Convert documents between formats |

---

## Type Definitions

### Message Format

```python
{
    "role": "user" | "assistant" | "system" | "tool",
    "content": str,
    "tool_calls": Optional[List[ToolCall]],  # For assistant messages
    "tool_call_id": Optional[str]  # For tool messages
}
```

### ToolCall Format

```python
{
    "id": str,
    "type": "function",
    "function": {
        "name": str,
        "arguments": str  # JSON string
    }
}
```

### MCP Configuration Format

```json
{
    "mcpServers": {
        "server_name": {
            "command": "executable",
            "args": ["arg1", "arg2"],
            "env": {
                "ENV_VAR": "value"
            }
        }
    }
}
```
