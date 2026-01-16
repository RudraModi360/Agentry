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

| Feature | Description |
|:--------|:------------|
| **Multiple LLM Providers** | Ollama (local/cloud), Groq, Google Gemini, Azure OpenAI |
| **Built-in Tools** | Filesystem, web search, code execution, document handling |
| **MCP Support** | Connect to external tool servers via Model Context Protocol |
| **Web and CLI Interfaces** | Modern web UI and feature-rich terminal interface |
| **Session Management** | Automatic save/restore of chat sessions |
| **Persistent Memory** | Extract and store insights from conversations |
| **Custom Tool Registration** | Easily register Python functions as agent tools |
| **Streaming Responses** | Real-time output for improved UX |

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

| Type | Flag | Description |
|:-----|:-----|:------------|
| Default | `--agent default` | Standard agent with all tools |
| Smart | `--agent smart` | Enhanced reasoning with project memory |
| Copilot | `--copilot` | Optimized for coding tasks |

### Available Options

| Option | Short | Description |
|:-------|:------|:------------|
| `--agent` | `-a` | Agent type: default, smart, copilot |
| `--copilot` | `-c` | Shortcut for --agent copilot |
| `--provider` | `-p` | LLM provider: ollama, groq, gemini, azure |
| `--model` | `-m` | Model name (provider-specific) |
| `--endpoint` | | Azure Endpoint URL |
| `--session` | `-s` | Session ID to resume |
| `--debug` | `-d` | Enable debug mode |
| `--list-models` | | List available models |
| `--help` | `-h` | Show help |

---

## Web Interface (GUI)

The web GUI provides a modern, browser-based chat experience.

```bash
agentry_gui
```

Once running, open your browser to `http://localhost:8000`.

### Features

- User authentication (login/register)
- Multi-provider configuration
- Chat sessions with history
- Image upload for vision-capable models
- Tool usage visualization
- MCP server configuration
- Light and dark themes

---

## Python Framework (Library)

Use Agentry directly in your Python code for custom applications.

### Basic Agent Example

```python
import asyncio
from agentry import Agent

async def main():
    # Create an agent with a specific provider
    agent = Agent(llm="ollama", model="llama3.2:3b")
    
    # Load default tools
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

| Provider | Type | API Key | Best For |
|:---------|:-----|:--------|:---------|
| Ollama | Local/Cloud | Optional | Development, privacy |
| Groq | Cloud | Required | Speed, production |
| Gemini | Cloud | Required | Multimodal tasks |
| Azure | Cloud | Required + Endpoint | Enterprise |

---

## Built-in Tools

| Category | Tools |
|:---------|:------|
| **Filesystem** | read_file, write_file, list_directory, delete_file, move_file, copy_file, make_directory |
| **Web** | web_search, scrape_webpage, fetch_url |
| **Execution** | run_shell_command, run_python_script |
| **Documents** | PDF, DOCX, PPTX, Excel, CSV, image handlers |

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
    ui/                 # Web interface
    memory/             # Persistent memory
    document_handlers/  # Document handlers
```

---

## Documentation

Complete documentation is available at: **[https://rudramodi360.github.io/Agentry/](https://rudramodi360.github.io/Agentry/)**

### Documentation Topics

| Topic | Description |
|:------|:------------|
| [Getting Started](https://rudramodi360.github.io/Agentry/getting-started) | Installation and first steps |
| [Core Concepts](https://rudramodi360.github.io/Agentry/core-concepts) | Agent loop, tools, providers |
| [API Reference](https://rudramodi360.github.io/Agentry/api-reference) | Complete API documentation |
| [Custom Tools](https://rudramodi360.github.io/Agentry/custom-tools) | Creating custom tools |
| [MCP Integration](https://rudramodi360.github.io/Agentry/mcp-integration) | External tool servers |
| [Session Management](https://rudramodi360.github.io/Agentry/session-management) | Working with sessions |
| [Examples](https://rudramodi360.github.io/Agentry/examples) | Code examples |
| [Troubleshooting](https://rudramodi360.github.io/Agentry/troubleshooting) | Common issues |

---

## Contributing

We welcome contributions. Please see the [Contributing Guide](https://rudramodi360.github.io/Agentry/CONTRIBUTING) for details.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Contact

- **GitHub Issues:** [Report issues](https://github.com/RudraModi360/Agentry/issues)
- **Discussions:** [Community discussions](https://github.com/RudraModi360/Agentry/discussions)
- **Email:** rudramodi9560@gmail.com
