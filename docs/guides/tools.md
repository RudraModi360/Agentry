---
title: Tools Guide
description: Creating and managing custom tools
---

# Tools Guide

Tools let agents interact with the world. This guide covers tool creation, registration, and management.

## Tool Basics

### What is a Tool?

A tool is a Python function that an agent can call to perform actions.

```python
def get_weather(city: str) -> str:
    """Get current weather for a city.
    
    Args:
        city: Name of the city
    
    Returns:
        Weather description
    """
    return f"Sunny, 72°F in {city}"
```

### Tool Requirements

1. **Type Hints**: Required for schema generation
2. **Docstring**: Required for LLM understanding
3. **Return Type**: Should return `str` or `ToolResult`

## Creating Tools

### Simple Function

```python
def calculate(expression: str) -> str:
    """Calculate a mathematical expression.
    
    Args:
        expression: Math expression (e.g., "2 + 2")
    
    Returns:
        Calculation result
    """
    return str(eval(expression))
```

### With Optional Parameters

```python
def search_web(query: str, num_results: int = 5) -> str:
    """Search the web for information.
    
    Args:
        query: Search query
        num_results: Number of results to return (default: 5)
    
    Returns:
        Search results
    """
    # Your search implementation
    return json.dumps(results)
```

### With Complex Types

```python
from typing import List, Optional
from pydantic import BaseModel

class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str

def search_database(
    query: str,
    filters: Optional[dict] = None,
    limit: int = 10
) -> List[SearchResult]:
    """Search database with filters.
    
    Args:
        query: Search query
        filters: Optional filter criteria
        limit: Maximum results
    
    Returns:
        List of search results
    """
    # Your implementation
    return results
```

## Tool Registration

### At Agent Creation

```python
agent = Agent(
    provider="ollama",
    tools=[get_weather, calculate, search_web]
)
```

### After Creation

```python
# Register function
agent.register_tool_from_function(get_weather)

# Register tool class
agent.add_custom_tool(MyCustomTool())
```

### Using Presets

```python
# Pre-configured tool sets
agent = Agent(tools="smart")    # Full agentic toolkit
agent = Agent(tools="copilot")  # Code-focused
agent = Agent(tools="lightweight")  # Basic tools
```

## Tool Classes

### BaseTool

For complex tools with state or dependencies:

```python
from logicore.tools import BaseTool, ToolResult

class DatabaseTool(BaseTool):
    name = "query_database"
    description = "Execute SQL queries on the database"
    
    def __init__(self, connection_string: str):
        self.connection = create_connection(connection_string)
    
    async def run(self, query: str, params: dict = None) -> ToolResult:
        """Execute a database query."""
        try:
            result = self.connection.execute(query, params)
            return ToolResult(
                success=True,
                content=json.dumps(result.fetchall())
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e)
            )
    
    def is_read_only(self) -> bool:
        """Check if query is read-only."""
        return query.strip().upper().startswith("SELECT")
```

### ToolResult

```python
from logicore.tools import ToolResult

# Success result
result = ToolResult(
    success=True,
    content="Operation completed",
    metadata={"rows_affected": 5}
)

# Error result
result = ToolResult(
    success=False,
    error="Permission denied"
)
```

## Tool Metadata

### Read-Only Tools

```python
class ReadFileTool(BaseTool):
    def is_read_only(self) -> bool:
        return True  # No approval needed
```

### Destructive Tools

```python
class DeleteFileTool(BaseTool):
    def is_destructive(self) -> bool:
        return True  # Always requires approval
```

### Concurrency Safe

```python
class LogTool(BaseTool):
    def is_concurrency_safe(self) -> bool:
        return True  # Can run in parallel
```

## Built-in Tools

### Filesystem

| Tool | Description |
|------|-------------|
| `read_file` | Read file contents |
| `write_file` | Create/overwrite file |
| `edit_file` | Edit file with diff |
| `delete_file` | Delete a file |
| `list_files` | List directory contents |
| `search_files` | Search files by pattern |
| `grep` | Search file contents |

### Web

| Tool | Description |
|------|-------------|
| `web_search` | Search the web |
| `url_fetch` | Fetch URL content |
| `image_search` | Search for images |

### Execution

| Tool | Description |
|------|-------------|
| `execute_command` | Run shell commands |
| `code_execute` | Run Python code |

### Git

| Tool | Description |
|------|-------------|
| `git_command` | Execute git operations |

### Task Management

| Tool | Description |
|------|-------------|
| `task_create` | Create a task |
| `task_get` | Get task details |
| `task_update` | Update task status |
| `task_list` | List all tasks |
| `task_next` | Get next task |

### Planning

| Tool | Description |
|------|-------------|
| `enter_plan_mode` | Start planning |
| `submit_plan` | Submit plan |
| `exit_plan_mode` | Exit planning |
| `view_plan` | View current plan |

## Tool Approval

### Approval System

```python
agent = Agent(
    provider="ollama",
    approval_timeout=120.0,  # Seconds to wait
    allow_tools={"read_file"}  # Pre-approved tools
)
```

### Approval Callback

```python
async def approve_tool(session_id: str, tool_name: str, args: dict) -> bool:
    """Custom approval logic."""
    if tool_name == "delete_file":
        return False  # Deny dangerous operations
    return True  # Approve everything else

agent.set_callbacks(on_tool_approval=approve_tool)
```

### Headless Mode

In non-interactive contexts, tools are auto-denied:

```python
# Running in a script (non-interactive)
agent = Agent(provider="ollama")

# Tools requiring approval will be denied
# Use allow_tools for pre-approved tools
agent = Agent(
    provider="ollama",
    allow_tools={"read_file", "write_file"}
)
```

## Tool Budget

When tool schemas exceed token limits, lower-priority tools are deferred:

```python
agent = Agent(
    provider="ollama",
    tools="full"  # Many tools
)

# System automatically manages tool budget
# Core tools always available
# MCP/plugin tools deferred if needed
```

## Best Practices

1. **Clear Docstrings**: Help LLM understand when to use the tool
2. **Type Hints**: Required for schema generation
3. **Error Handling**: Return meaningful error messages
4. **Read-Only Checks**: Mark read-only tools for auto-approval
5. **Concurrency**: Mark safe tools for parallel execution
6. **Validation**: Validate inputs in tool implementation

## Next Steps

- [Custom Tool Examples](../examples/custom_tools.py)
- [Tool Registry API](../api/tools.md)
- [Skills Guide](./skills.md)
- [Architecture](./architecture.md)
