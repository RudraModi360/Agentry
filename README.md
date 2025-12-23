# Agentry Community

Agentry Community (`agentry_community`) is a professional, modular AI agent framework designed for developers who need flexibility, privacy, and ease of integration. It provides a robust SDK to build specialized AI agents with support for custom tooling, multi-provider LLM integration, and extensible memory systems.

## Key Features

- **Multi-Provider Support**: Seamlessly switch between Ollama, Groq, and Google Gemini.
- **Specialized Agents**: 
  - `Agent`: Standard base agent for general tasks.
  - `SmartAgent`: Advanced agent with enhanced reasoning and tool-selection logic.
  - `CopilotAgent`: Tailored for software development and code refactoring.
  - `MCPAgent`: Native integration with the Model Context Protocol (MCP).
- **Custom Tooling**: Register any Python function as a tool with automatic schema generation.
- **Privacy First**: Optimized for local-first workflows with Ollama support.

## Installation

```bash
pip install agentry_community
```

## Quick Start

Initialize a basic agent and start a conversation:

```python
import asyncio
from agentry import Agent

async def main():
    # Initialize using Ollama (default)
    agent = Agent(llm="ollama", model="llama3.2")
    
    # Execute a simple chat request
    response = await agent.chat("Explain quantum entanglement in one sentence.")
    print(f"Assistant: {response}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Custom Tool Integration

Agentry makes it simple to extend agent capabilities by registering Python functions. The framework automatically parses docstrings and type hints to generate the necessary tool schemas.

```python
from agentry import Agent

def get_market_price(ticker: str) -> str:
    """
    Fetch the current market price for a given stock ticker.
    
    Args:
        ticker: The stock symbol (e.g., 'AAPL', 'GOOGL').
    """
    # Integration logic here
    return f"The current price for {ticker} is $150.00"

async def run_market_agent():
    agent = Agent(llm="groq", model="mixtral-8x7b-32768")
    
    # Register the custom tool
    agent.register_tool_from_function(get_market_price)
    
    # The agent will now use the tool when appropriate
    response = await agent.chat("What is the price of AAPL right now?")
    print(response)
```

## Advanced Agent Types

Agentry provides specialized agent classes for different use cases:

- **SmartAgent**: Handles complex multi-step reasoning.
- **CopilotAgent**: Optimized for code analysis and generation.
- **MCPAgent**: Connects to external Model Context Protocol servers for enterprise-grade tool integration.

## Documentation

For detailed guides and API references, please refer to the `docs/` directory:

- [Getting Started](docs/getting-started.md)
- [Custom Tools Development](docs/custom-tools.md)
- [Framework Usage SDK](docs/framework-usage.md)
- [API Reference](docs/api-reference.md)
- [MCP Integration](docs/mcp-integration.md)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
