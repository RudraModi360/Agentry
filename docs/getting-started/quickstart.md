---
title: Quickstart
description: Build your first AI agent in 5 minutes
---

# Quickstart

Build a tool-enabled AI agent in 5 minutes.

## Step 1: Install Logicore

```bash
pip install logicore
```

## Step 2: Create Your Agent

Create a file `my_agent.py`:

```python
import asyncio
from logicore import Agent

# Define a custom tool
def calculate(expression: str) -> str:
    """Calculate a mathematical expression.
    
    Args:
        expression: Mathematical expression to evaluate (e.g., "2 + 2")
    
    Returns:
        The result of the calculation
    """
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {e}"

async def main():
    # Create agent with your tool
    agent = Agent(
        provider="ollama",
        model="qwen3.5:0.8b",
        role="Math Assistant",
        tools=[calculate]
    )
    
    # Chat with the agent
    response = await agent.chat("What is 15 * 23?")
    print(response["content"])

if __name__ == "__main__":
    asyncio.run(main())
```

## Step 3: Run It

```bash
python my_agent.py
```

The agent will use the `calculate` tool to solve the math problem.

## What Just Happened?

1. **Agent Creation**: You created an `Agent` with Ollama as the provider
2. **Tool Registration**: The `calculate` function was auto-registered as an LLM tool
3. **Auto-Schema**: Logicore parsed the type hints and docstring into a JSON schema
4. **Tool Execution**: The agent decided to use your tool and executed it

## Adding More Features

### Streaming Responses

```python
async def main():
    agent = Agent(
        provider="ollama",
        model="qwen3.5:0.8b",
        tools=[calculate]
    )
    
    # Stream tokens in real-time
    async def on_token(token):
        print(token, end="", flush=True)
    
    await agent.chat(
        "What is 15 * 23?",
        callbacks={"on_token": on_token},
        stream=True
    )
```

### Using Tool Presets

```python
# Use pre-configured tool sets
agent = Agent(
    provider="ollama",
    model="qwen3.5:0.8b",
    tools="smart"  # Full agentic toolkit
)
```

### Adding Skills

```python
agent = Agent(
    provider="ollama",
    model="qwen3.5:0.8b",
    skills=["excel_operations"]  # Load Excel skills
)
```

### Multiple Tools

```python
def search_web(query: str) -> str:
    """Search the web for information."""
    return f"Results for: {query}"

def read_file(path: str) -> str:
    """Read contents of a file."""
    with open(path) as f:
        return f.read()

agent = Agent(
    provider="ollama",
    model="qwen3.5:0.8b",
    tools=[calculate, search_web, read_file]
)
```

## Next Steps

1. [Core Concepts](./concepts.md) - Understand agents, tools, and skills
2. [Agent Guide](../guides/agents.md) - Learn about agent variants
3. [Tools Guide](../guides/tools.md) - Master custom tool creation
4. [Skills Guide](../guides/skills.md) - Build reusable skill packs
5. [Examples](https://github.com/RudraModi360/Agentry/tree/main/examples) - More code samples
