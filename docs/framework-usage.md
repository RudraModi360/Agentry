# Scratchy Framework Documentation
## *The Python SDK*

Build your own AI applications by importing Scratchy as a library.

### Basic Usage

```python
import asyncio
from scratchy import Agent

async def main():
    agent = Agent(llm="ollama", model="llama3.2")
    
    # Simple chat
    response = await agent.chat("Calculate 25 * 48")
    print(response)

asyncio.run(main())
```

### Adding Custom Tools

You can register any Python function as a tool:

```python
from scratchy import Agent
from scratchy.tools import register_tool_from_function

def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    return f"The weather in {city} is Sunny."

async def main():
    agent = Agent(llm="ollama")
    
    # Register tool
    await agent.register_tool(get_weather)
    
    # The agent now knows how to use it!
    await agent.chat("What's the weather in Tokyo?")

```

### Multi-Agent Systems

Scratchy supports specialized agents like `CopilotAgent` which is optimized for coding tasks:

```python
from scratchy import CopilotAgent

coder = CopilotAgent(llm="groq", api_key="...")
await coder.chat("Refactor this code for performance...")
```
