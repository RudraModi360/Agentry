# BasicAgent - Build Your Own AI Agent

The **BasicAgent** is a generic, customizable wrapper around the Agentry framework. It provides a clean, LangChain-style API for creating custom AI agents with your own tools.

## Quick Start

```python
import asyncio
from agentry.agents import BasicAgent

# Create a simple agent
agent = BasicAgent(
    name="MyBot",
    description="A helpful assistant",
    provider="ollama",
    model="llama3.2:3b"
)

# Chat with it
async def main():
    response = await agent.chat("Hello! What can you do?")
    print(response)

asyncio.run(main())
```

## Adding Custom Tools

Tools can be regular Python functions:

```python
from agentry.agents import BasicAgent, tool

# Define tools as functions
def calculator(expression: str) -> str:
    """Calculate a math expression."""
    return str(eval(expression))

def get_weather(city: str) -> str:
    """Get the weather for a city."""
    # In reality, you'd call a weather API
    return f"Weather in {city}: 25°C, Sunny"

@tool("Search the database for records")
def search_database(query: str, limit: int = 10) -> str:
    """Search function with decorator."""
    return f"Found {limit} results for: {query}"

# Create agent with tools
agent = BasicAgent(
    name="UtilityBot",
    description="A bot that can calculate, check weather, and search",
    provider="groq",
    model="llama-3.3-70b-versatile",
    api_key="your-api-key",
    tools=[calculator, get_weather, search_database]
)

# The agent will use tools automatically
response = await agent.chat("What's 15 * 23?")
# Agent will call calculator("15 * 23") and return "345"
```

## Using the Convenience Function

```python
from agentry.agents import create_agent

agent = create_agent(
    name="ResearchBot",
    description="Helps with research tasks",
    tools=[search_web, summarize_text],
    provider="gemini",
    model="gemini-2.0-flash",
    api_key="your-api-key"
)
```

## Full Configuration Options

```python
agent = BasicAgent(
    # Required
    name="AgentName",              # Name of your agent
    description="What it does",    # Used in system prompt
    
    # LLM Configuration
    provider="ollama",             # "ollama", "groq", or "gemini"
    model="llama3.2:3b",          # Model name (provider-specific)
    api_key=None,                  # API key for cloud providers
    
    # Tools
    tools=[func1, func2],          # List of functions or BaseTool instances
    
    # Advanced
    system_prompt=None,            # Custom system prompt (optional)
    memory_enabled=True,           # Use memory middleware
    debug=False,                   # Enable debug logging
    max_iterations=20              # Max tool call iterations per chat
)
```

## Streaming Responses

```python
agent = BasicAgent(name="StreamBot", provider="groq", model="llama-3.3-70b-versatile")

# Set callbacks for streaming
agent.set_callbacks(
    on_token=lambda token: print(token, end="", flush=True),
    on_tool_start=lambda sid, name, args: print(f"\n[Using {name}...]"),
    on_tool_end=lambda sid, name, result: print(f"\n[{name} done]"),
    on_final_message=lambda sid, msg: print("\n[Complete]")
)

response = await agent.chat("Tell me about Python")
```

## Managing Sessions

```python
# Different sessions maintain separate context
await agent.chat("My name is Alice", session_id="user_1")
await agent.chat("What's my name?", session_id="user_1")  # "Alice"
await agent.chat("What's my name?", session_id="user_2")  # Doesn't know

# Clear session history
agent.clear_history(session_id="user_1")
```

## Creating Tools from Classes

For complex tools, use the BaseTool class:

```python
from agentry.tools.base import BaseTool, ToolResult
from pydantic import BaseModel, Field

class EmailArgs(BaseModel):
    to: str = Field(description="Recipient email address")
    subject: str = Field(description="Email subject")
    body: str = Field(description="Email body content")

class SendEmailTool(BaseTool):
    name = "send_email"
    description = "Send an email to someone"
    args_schema = EmailArgs
    
    def run(self, to: str, subject: str, body: str) -> ToolResult:
        # Your email sending logic here
        return ToolResult(success=True, content=f"Email sent to {to}")

# Use it
agent = BasicAgent(
    name="EmailBot",
    tools=[SendEmailTool()]
)
```

## Synchronous Usage

For scripts that don't use async:

```python
from agentry.agents import BasicAgent

agent = BasicAgent(name="SyncBot", provider="ollama")

# Use chat_sync instead of chat
response = agent.chat_sync("Hello!")
print(response)
```

## Adding Tools Dynamically

```python
agent = BasicAgent(name="FlexBot")

# Add one tool
agent.add_tool(my_function)

# Add multiple tools
agent.add_tools([func1, func2, func3])

# Check registered tools
print(agent.tools)  # ['my_function', 'func1', 'func2', 'func3']
```

## Examples

### Research Assistant

```python
from agentry.agents import BasicAgent

def web_search(query: str) -> str:
    """Search the web for information."""
    # Use your preferred search API
    from agentry.tools.web import WebSearchTool
    tool = WebSearchTool()
    result = tool.run(user_input=query, search_type="quick")
    return result.get("content", "No results")

def summarize(text: str, max_words: int = 100) -> str:
    """Summarize text to key points."""
    words = text.split()[:max_words]
    return " ".join(words) + "..."

agent = BasicAgent(
    name="ResearchBot",
    description="I help research topics and summarize findings",
    tools=[web_search, summarize],
    provider="groq",
    model="llama-3.3-70b-versatile"
)
```

### Code Helper

```python
import subprocess

def run_python(code: str) -> str:
    """Execute Python code and return output."""
    try:
        result = subprocess.run(
            ["python", "-c", code],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout or result.stderr
    except Exception as e:
        return str(e)

def read_file(path: str) -> str:
    """Read contents of a file."""
    with open(path, 'r') as f:
        return f.read()

agent = BasicAgent(
    name="CodeHelper",
    description="I help write and run Python code",
    tools=[run_python, read_file],
    provider="ollama",
    model="codellama:13b"
)
```

### Customer Service Bot

```python
def get_order_status(order_id: str) -> str:
    """Check status of an order."""
    # Query your database
    return f"Order {order_id}: Shipped, arriving tomorrow"

def create_ticket(issue: str, priority: str = "normal") -> str:
    """Create a support ticket."""
    return f"Ticket created: {issue} (Priority: {priority})"

def get_faq(topic: str) -> str:
    """Get FAQ for a topic."""
    faqs = {
        "returns": "You can return items within 30 days...",
        "shipping": "Standard shipping takes 3-5 business days...",
    }
    return faqs.get(topic, "No FAQ found for that topic")

agent = BasicAgent(
    name="SupportBot",
    description="I help customers with orders and support",
    tools=[get_order_status, create_ticket, get_faq],
    provider="groq",
    model="llama-3.1-8b-instant"
)
```

## Architecture

```
BasicAgent
├── Wraps Agent class
├── Auto-converts functions to tools
│   ├── Extracts function signature
│   ├── Builds JSON schema
│   └── Creates executor wrapper
├── Generates system prompt from name/description
└── Exposes simple API
    ├── chat() - async
    ├── chat_sync() - sync
    ├── add_tool() - dynamic
    └── set_callbacks() - streaming
```

## Best Practices

1. **Write clear docstrings** - They become tool descriptions for the LLM
2. **Use type hints** - They improve tool schema generation
3. **Keep tools focused** - One tool, one purpose
4. **Handle errors gracefully** - Return helpful error messages
5. **Use appropriate models** - Smaller models for simple tasks, larger for complex reasoning
