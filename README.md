# Agentry

**A Modular AI Agent Framework for Python**

Agentry (published as `agentry_community` on PyPI) is a powerful, privacy-focused AI agent framework designed for flexibility and ease of use. It provides a unified interface to interact with multiple LLM providers, a comprehensive set of built-in tools, and support for the Model Context Protocol (MCP).

---

## Table of Contents

1.  [Features](#features)
2.  [Installation](#installation)
3.  [Quick Start](#quick-start)
4.  [Command-Line Interface (CLI)](#command-line-interface-cli)
5.  [Web Interface (GUI)](#web-interface-gui)
6.  [Python Framework (Library)](#python-framework-library)
7.  [Supported Providers](#supported-providers)
8.  [Built-in Tools](#built-in-tools)
9.  [MCP Integration](#mcp-integration)
10. [Project Structure](#project-structure)
11. [Documentation](#documentation)
12. [Contributing](#contributing)
13. [License](#license)

---

## Features

-   **Multiple LLM Providers**: Supports Ollama (local and cloud), Groq, Google Gemini, and Azure OpenAI (including Azure AI Foundry models like Claude).
-   **Built-in Tools**: Comes with a rich set of tools for filesystem operations, web search, code execution, and document handling (PDF, DOCX, PPTX, Excel).
-   **MCP Support**: Connect to external tool servers via the Model Context Protocol for extensibility.
-   **Web and CLI Interfaces**: Offers both a modern web-based chat UI and a feature-rich terminal interface.
-   **Session Management**: Automatically saves and restores chat sessions.
-   **Persistent Memory**: Includes a memory middleware that extracts and stores insights from conversations for long-term context.
-   **Custom Tool Registration**: Easily register Python functions as agent tools.
-   **Streaming Responses**: Supports streaming responses for real-time output.

---

## Installation

### From PyPI

```bash
pip install agentry_community
```

### From Source (for development)

```bash
# Clone the repository
git clone https://github.com/RudraModi360/Agentry.git
cd Agentry

# Create a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate  # On Windows
# source .venv/bin/activate  # On Linux/macOS

# Install in editable mode
pip install -e .
```

---

## Quick Start

After installation, you can immediately start using Agentry via the CLI or GUI.

**Launch the CLI:**
```bash
agentry_cli
```

**Launch the Web GUI:**
```bash
agentry_gui
```

---

## Command-Line Interface (CLI)

The CLI provides a powerful terminal-based interface for interacting with the agent.

### Basic Usage

```bash
# Start with default settings (Ollama provider)
agentry_cli

# Use a specific provider and model
agentry_cli -p groq -m llama-3.3-70b-versatile

# Use Google Gemini
agentry_cli -p gemini -m gemini-2.0-flash

# Use Azure OpenAI
agentry_cli -p azure --endpoint https://your-resource.openai.azure.com -m gpt-4
```

### Agent Types

-   `--agent default` (or `-a default`): Standard agent with all tools.
-   `--agent smart` (or `-a smart`): Enhanced reasoning with project memory.
-   `--agent copilot` (or `-c`): Optimized for coding tasks.

### Available Options

| Option          | Short | Description                                       |
| --------------- | ----- | ------------------------------------------------- |
| `--agent`       | `-a`  | Agent type: `default`, `smart`, `copilot`         |
| `--copilot`     | `-c`  | Shortcut for `--agent copilot`                    |
| `--provider`    | `-p`  | LLM provider: `ollama`, `groq`, `gemini`, `azure` |
| `--model`       | `-m`  | Model name (provider-specific)                    |
| `--endpoint`    |       | Azure Endpoint URL                                |
| `--session`     | `-s`  | Session ID to resume                              |
| `--debug`       | `-d`  | Enable debug mode                                 |
| `--list-models` |       | List available models                             |
| `--help`        | `-h`  | Show help                                         |

---

## Web Interface (GUI)

The web GUI provides a modern, browser-based chat experience.

```bash
agentry_gui
```

Once running, open your browser to `http://localhost:8000`.

### Features of the Web UI

-   User authentication (login/register)
-   Multi-provider configuration (Ollama, Groq, Gemini, Azure)
-   Chat sessions with history
-   Image upload for vision-capable models
-   Tool usage visualization
-   MCP server configuration
-   Light and dark themes

---

## Python Framework (Library)

You can use Agentry directly in your Python code for custom applications.

### Basic Agent Example

```python
import asyncio
from agentry import Agent

async def main():
    # Create an agent with a specific provider
    agent = Agent(llm="ollama", model="llama3.2:3b")
    
    # Load default tools (filesystem, web, execution)
    agent.load_default_tools()
    
    # Chat with the agent
    response = await agent.chat("What is the current directory?")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
```

### Using Different Providers

```python
from agentry import Agent

# Groq
agent = Agent(llm="groq", model="llama-3.3-70b-versatile", api_key="your-api-key")

# Gemini
agent = Agent(llm="gemini", model="gemini-2.0-flash", api_key="your-api-key")

# Azure OpenAI
agent = Agent(
    llm="azure",
    model="gpt-4",
    api_key="your-api-key",
    endpoint="https://your-resource.openai.azure.com"
)
```

### Registering Custom Tools

```python
from agentry import Agent

agent = Agent(llm="ollama")
agent.load_default_tools()

def calculate_bmi(weight_kg: float, height_m: float) -> str:
    """
    Calculates BMI given weight in kg and height in meters.
    Returns the BMI value and category.
    """
    bmi = weight_kg / (height_m ** 2)
    category = "Normal"
    if bmi < 18.5:
        category = "Underweight"
    elif bmi > 25:
        category = "Overweight"
    return f"BMI: {bmi:.2f} ({category})"

# Register the function as a tool
agent.register_tool_from_function(calculate_bmi)
```

### Using MCP Servers

```python
import asyncio
from agentry import Agent

async def main():
    agent = Agent(llm="ollama")
    agent.load_default_tools()
    
    # Add tools from an MCP server configuration file
    await agent.add_mcp_server("mcp.json")
    
    response = await agent.chat("Use the excel tool to read data from my spreadsheet.")
    print(response)

asyncio.run(main())
```

---

## Supported Providers

| Provider | Description                          | Requires API Key |
| -------- | ------------------------------------ | ---------------- |
| Ollama   | Local models or Ollama Cloud         | Optional (cloud) |
| Groq     | Ultra-fast inference via LPU         | Yes              |
| Gemini   | Google AI models                     | Yes              |
| Azure    | Azure OpenAI and Azure AI Foundry    | Yes + Endpoint   |

---

## Built-in Tools

Agentry includes multiple tool categories:

-   **Filesystem**: `read_file`, `write_file`, `list_directory`, `delete_file`, `move_file`, `copy_file`, `make_directory`
-   **Web**: `web_search`, `scrape_webpage`, `fetch_url`
-   **Execution**: `run_shell_command`, `run_python_script`
-   **Document Handlers**: Support for PDF, DOCX, PPTX, Excel, CSV, and image files

---

## MCP Integration

Agentry supports the Model Context Protocol (MCP) for connecting to external tool servers.

Create an `mcp.json` file in your project root:

```json
{
  "mcpServers": {
    "excel": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-excel"]
    }
  }
}
```

The agent will automatically discover and use tools from connected MCP servers.

---

## Project Structure

```
agentry/
    __init__.py         # Package exports
    cli.py              # CLI entry point
    gui.py              # GUI entry point
    agents/             # Agent implementations
        agent.py        # Base Agent class
        copilot.py      # CopilotAgent
        agent_smart.py  # SmartAgent
    providers/          # LLM provider implementations
        ollama_provider.py
        groq_provider.py
        gemini_provider.py
        azure_provider.py
    tools/              # Built-in tools
    ui/                 # Web interface (FastAPI server, HTML/CSS/JS)
    memory/             # Persistent memory and context management
    document_handlers/  # PDF, DOCX, PPTX, Excel handlers
```

---

## Documentation

For detailed documentation, see the `docs/` directory in the repository:

-   [Getting Started](https://github.com/RudraModi360/Agentry/blob/main/docs/getting-started.md)
-   [Core Concepts](https://github.com/RudraModi360/Agentry/blob/main/docs/core-concepts.md)
-   [API Reference](https://github.com/RudraModi360/Agentry/blob/main/docs/api-reference.md)
-   [Custom Tools](https://github.com/RudraModi360/Agentry/blob/main/docs/custom-tools.md)
-   [MCP Integration](https://github.com/RudraModi360/Agentry/blob/main/docs/mcp-integration.md)
-   [Session Management](https://github.com/RudraModi360/Agentry/blob/main/docs/session-management.md)
-   [Troubleshooting](https://github.com/RudraModi360/Agentry/blob/main/docs/troubleshooting.md)

---

## Contributing

We welcome contributions. Please see the [Contributing Guide](https://github.com/RudraModi360/Agentry/blob/main/docs/CONTRIBUTING.md) for details on how to get started.

---

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/RudraModi360/Agentry/blob/main/LICENSE) file for details.
