# API Reference

Complete API documentation for the Scratchy framework.

## Agent Class

The main agent class that handles LLM interactions, tool management, and session persistence.

### Constructor

```python
Agent(
    llm: Union[LLMProvider, str] = "ollama",
    model: str = None,
    api_key: str = None,
    system_message: str = None,
    role: str = "general",
    debug: bool = False,
    max_iterations: int = 20
)
```

**Parameters:**
- `llm`: LLM provider ("ollama", "groq", "gemini") or LLMProvider instance
- `model`: Model name (e.g., "llama3.2", "llama-3.3-70b-versatile")
- `api_key`: API key for cloud providers (Groq, Gemini)
- `system_message`: Custom system prompt (overrides role-based prompt)
- `role`: Agent role ("general" or "engineer") for default prompt
- `debug`: Enable debug logging
- `max_iterations`: Maximum tool execution iterations per chat

**Example:**
```python
agent = Agent(
    llm="ollama",
    model="llama3.2",
    role="general",
    debug=True
)
```

### Methods

#### `load_default_tools()`
Load all built-in tools (filesystem, web, execution).

```python
agent.load_default_tools()
```

#### `register_tool_from_function(func: Callable)`
Register a Python function as a tool. Automatically generates schema from function signature.

```python
def calculate_bmi(weight_kg: float, height_m: float) -> str:
    """Calculate BMI given weight and height."""
    bmi = weight_kg / (height_m ** 2)
    return f"BMI: {bmi:.2f}"

agent.register_tool_from_function(calculate_bmi)
```

#### `add_custom_tool(schema: Dict, executor: Callable)`
Add a custom tool with manual schema definition.

```python
schema = {
    "type": "function",
    "function": {
        "name": "my_tool",
        "description": "My custom tool",
        "parameters": {
            "type": "object",
            "properties": {
                "param": {"type": "string"}
            }
        }
    }
}

agent.add_custom_tool(schema, my_executor_function)
```

#### `async add_mcp_server(config_path: str)`
Connect to MCP servers defined in a config file.

```python
await agent.add_mcp_server("mcp.json")
```

#### `async chat(user_input: str, session_id: str = "default") -> str`
Main chat interface. Sends message and returns response.

```python
response = await agent.chat("Hello!", session_id="my_session")
```

#### `get_session(session_id: str) -> AgentSession`
Get or create a session.

```python
session = agent.get_session("my_session")
print(f"Messages: {len(session.messages)}")
```

#### `clear_session(session_id: str)`
Clear session history.

```python
agent.clear_session("my_session")
```

#### `set_callbacks(**kwargs)`
Set event callbacks.

```python
def on_tool_start(session_id, name, args):
    print(f"Tool: {name}")

agent.set_callbacks(on_tool_start=on_tool_start)
```

**Available callbacks:**
- `on_tool_start(session_id, name, args)`
- `on_tool_end(session_id, name, result)`
- `on_tool_approval(session_id, name, args) -> bool` (async)
- `on_final_message(session_id, content)`

#### `async cleanup()`
Cleanup resources (close MCP connections).

```python
await agent.cleanup()
```

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

Automatically:
- Uses "engineer" role for coding-focused prompts
- Loads default tools

### Additional Methods

#### `async explain_code(code: str) -> str`
Explain a code snippet.

```python
explanation = await copilot.explain_code("""
def factorial(n):
    return 1 if n <= 1 else n * factorial(n-1)
""")
```

#### `async review_file(filepath: str) -> str`
Review a file for bugs and improvements.

```python
review = await copilot.review_file("my_script.py")
```

#### `async general_chat(user_input: str) -> str`
Switch to general assistant mode (separate session).

```python
response = await copilot.general_chat("Tell me a joke")
```

---

## SessionManager Class

Manages session persistence with .toon format.

### Constructor

```python
SessionManager(history_dir: str = None)
```

**Parameters:**
- `history_dir`: Directory for session files (default: `scratchy/session_history/`)

### Methods

#### `save_session(session_id: str, messages: List[Dict])`
Save session to .toon file.

```python
sm.save_session("my_session", session.messages)
```

#### `load_session(session_id: str) -> Optional[List[Dict]]`
Load session from .toon file.

```python
messages = sm.load_session("my_session")
```

#### `list_sessions() -> List[Dict]`
List all saved sessions.

```python
sessions = sm.list_sessions()
for s in sessions:
    print(f"{s['id']}: {s['message_count']} messages")
```

#### `delete_session(session_id: str) -> bool`
Delete a session file.

```python
sm.delete_session("old_session")
```

#### `session_exists(session_id: str) -> bool`
Check if session exists.

```python
if sm.session_exists("my_session"):
    print("Session found!")
```

---

## AgentSession Class

Represents a conversation session.

### Attributes

- `session_id: str` - Session identifier
- `messages: List[Dict]` - Message history
- `created_at: datetime` - Creation timestamp
- `last_activity: datetime` - Last activity timestamp
- `metadata: Dict` - Custom metadata

### Methods

#### `add_message(message: Dict)`
Add message to session.

```python
session.add_message({"role": "user", "content": "Hello"})
```

#### `clear_history(keep_system: bool = True)`
Clear message history.

```python
session.clear_history()
```

---

## Providers

### OllamaProvider

```python
from scratchy.providers import OllamaProvider

provider = OllamaProvider(
    model="llama3.2",
    host="http://localhost:11434"
)
```

### GroqProvider

```python
from scratchy.providers import GroqProvider

provider = GroqProvider(
    model="llama-3.3-70b-versatile",
    api_key="your-api-key"
)
```

### GeminiProvider

```python
from scratchy.providers import GeminiProvider

provider = GeminiProvider(
    model="gemini-pro",
    api_key="your-api-key"
)
```

---

## Built-in Tools

### Filesystem Tools
- `read_file` - Read file contents
- `create_file` - Create new files
- `edit_file` - Modify existing files
- `delete_file` - Remove files
- `list_files` - Browse directories
- `search_files` - Find text in files
- `fast_grep` - Quick keyword search

### Execution Tools
- `execute_command` - Run shell commands
- `code_execute` - Execute Python code

### Web Tools
- `web_search` - Search the web
- `url_fetch` - Fetch URL content

### Git Tools
- `git_command` - Execute Git operations (status, commit, log, etc.)

### Document Tools
- `pandoc_convert` - Convert documents between formats using Pandoc

For detailed tool schemas, see the [source code](../scratchy/tools/).
