# Agentry Documentation

Welcome to the Agentry documentation! This guide will help you understand and use the Agentry AI Agent Framework.

## 📚 Table of Contents

### Getting Started
- [Installation & Setup](getting-started.md) - Get up and running quickly
- [Your First Agent](getting-started.md#your-first-agent) - Hello World example
- [Quick Examples](getting-started.md#quick-examples) - Common use cases

### Core Documentation
- [API Reference](api-reference.md) - Complete API documentation
  - [Agent Class](api-reference.md#agent-class)
  - [CopilotAgent Class](api-reference.md#copilotagent-class)
  - [SessionManager Class](api-reference.md#sessionmanager-class)
  - [Providers](api-reference.md#providers)
  - [Built-in Tools](api-reference.md#built-in-tools)

- [Session Management](session-management.md) - Working with sessions
  - [Basic Usage](session-management.md#basic-usage)
  - [Interactive Mode](session-management.md#interactive-mode)
  - [Multi-Session](session-management.md#multi-session-management)
  - [File Format](session-management.md#session-files)

### Advanced Topics
- Custom Tools *(coming soon)* - Create your own tools
- MCP Integration *(coming soon)* - Connect external MCP servers
- Examples *(coming soon)* - Code examples and recipes
- Core Concepts *(coming soon)* - Architecture deep dive
- Troubleshooting *(coming soon)* - Common issues and solutions

## Quick Links

### For Beginners
- [Installation Guide](getting-started.md#installation)
- [Your First Agent](getting-started.md#your-first-agent)
- [Understanding Sessions](session-management.md#overview)

### For Developers
- [Agent API](api-reference.md#agent-class)
- [Custom Tool Registration](api-reference.md#register_tool_from_function)
- [Provider Configuration](api-reference.md#providers)

### For Advanced Users
- [Session Persistence](session-management.md#session-files)
- [Multi-Session Management](session-management.md#multi-session-management)
- [Source Code Exploration](../Agentry/)

## What is Agentry?

Agentry is a **one-stop Python-based solution** for understanding how real-world AI agents are built. It's designed for:

- **🌱 Beginners**: Learn by doing with clear, documented examples
- **🚀 Intermediate**: Build production-ready agents with best practices
- **🔬 Experts**: Deep dive into internals and extend the framework

### Key Features

- **Unified Agent Architecture**: Single `Agent` class supporting internal, MCP, and custom tools
- **Session Management**: Persistent chat history with `.toon` format in `Agentry/session_history/`
- **Custom Tool Support**: Easy function-to-tool conversion via `register_tool_from_function()`
- **Multiple LLM Providers**: Ollama, Groq, and Gemini support
- **Specialized Agents**: Pre-configured agents like `CopilotAgent` for coding

## Module Structure

```
Agentry/                      # Main package
├── agents/                   # Agent implementations
│   ├── agent.py             # Core Agent class
│   ├── copilot.py           # CopilotAgent (coding specialist)
│   └── agent_mcp.py         # Legacy MCP agent
├── providers/               # LLM provider implementations
│   ├── ollama_provider.py   # Ollama integration
│   ├── groq_provider.py     # Groq integration
│   └── gemini_provider.py   # Gemini integration
├── tools/                   # Built-in tools
│   ├── filesystem.py        # File operations
│   ├── execution.py         # Code/command execution
│   ├── web.py              # Web search & fetch
│   └── registry.py         # Tool registration
├── config/                  # Configuration
│   ├── prompts.py          # System prompts
│   └── settings.py         # API keys & settings
├── session_history/         # Saved chat sessions (.toon)
├── session_manager.py       # Session persistence
└── mcp_client.py           # MCP server integration
```

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                   User Code                     │
│         from Agentry import Agent              │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│          Agentry.agents.Agent                  │
│  ┌──────────────────────────────────────────┐  │
│  │    Session Management (AgentSession)     │  │
│  │    • Agentry/session_history/*.toon     │  │
│  └──────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────┐  │
│  │         Tool Management                  │  │
│  │  • Internal (Agentry/tools/)            │  │
│  │  • MCP (Agentry/mcp_client.py)          │  │
│  │  • Custom (register_tool_from_function)  │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│       Agentry.providers.LLMProvider            │
│    Ollama  │  Groq  │  Gemini                  │
└─────────────────────────────────────────────────┘
```

## Quick Start

```python
from Agentry import Agent

# Initialize
agent = Agent(llm="ollama", model="llama3.2")
agent.load_default_tools()

# Chat
response = await agent.chat("Hello!")
```

See [Getting Started](getting-started.md) for detailed instructions.

## Contributing

We welcome contributions! Please see our [Contributing Guide](../CONTRIBUTING.md) for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/RudraModi360/Agentry/issues)
- **Discussions**: [GitHub Discussions](https://github.com/RudraModi360/Agentry/discussions)
- **Email**: rudramodi9560@gmail.com

## License

MIT License - see [LICENSE](../LICENSE) for details.

---

**Built with ❤️ by [Rudra Modi](mailto:rudramodi9560@gmail.com)**

*Evolving towards the future of voice-driven AI assistants*
