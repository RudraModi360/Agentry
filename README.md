<p align="center">
    <img src="./logo/readme-hero.png" alt="Logicore Banner" width="420" style="max-width:60%; height:auto;" />
</p>

<p align="center">
    <a href="https://rudramodi360.github.io/Agentry/"><img src="https://img.shields.io/badge/Docs-Live-blue.svg" alt="Documentation" /></a>
    <a href="https://discord.gg/Yz8yFzgQ"><img src="https://img.shields.io/badge/Discord-Join-7289DA.svg" alt="Discord" /></a>
    <a href="https://pypi.org/project/logicore/"><img src="https://img.shields.io/pypi/v/logicore.svg" alt="PyPI" /></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License" /></a>
</p>

<p align="center">
    <strong>Enterprise-grade Python framework for building autonomous AI agents</strong><br>
    Multi-provider support • Native streaming • Persistent memory • Zero vendor lock-in
</p>

---

## What is Logicore?

Logicore is a unified agentic framework that lets you build AI agents **once** and deploy them across any LLM provider—Ollama, OpenAI, Gemini, Groq, or Azure—without rewriting a single line of code.

### The Problem It Solves

| Challenge | Traditional Approach | Logicore Solution |
|-----------|----------------------|-------------------|
| Provider Lock-in | Rewrite for each LLM | Single parameter swap |
| Tool Complexity | Manual JSON schemas | Auto-generate from Python functions |
| Token Management | DIY streaming | Native streaming + reasoning extraction |
| Memory Systems | Custom vector DBs | Built-in persistent memory with RAG |
| Scheduling | External cron/Celery | Native agent-aware scheduler |
| Approval Workflows | Custom per-app | Declarative approval system |

---

## Quickstart

### 1. Install

```bash
pip install logicore
```

### 2. Run Your First Agent

```python
import asyncio
from logicore import Agent

def check_weather(location: str) -> str:
    """Check weather for a location."""
    return "72°F and sunny" if "seattle" in location.lower() else "65°F cloudy"

async def main():
    agent = Agent(
        provider="ollama",
        model="qwen3.5:0.8b",
        role="Weather Assistant",
        tools=[check_weather]
    )
    
    response = await agent.chat("What's the weather in Seattle?")
    print(response["content"])

asyncio.run(main())
```

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Multi-Provider** | Switch between Ollama, OpenAI, Gemini, Groq, Azure with zero code changes |
| **Auto-Tool Generation** | Convert any Python function to an LLM tool automatically |
| **Native Streaming** | Real-time token updates + hidden reasoning extraction |
| **Persistent Memory** | Agents remember context across sessions with semantic search |
| **Cron Scheduler** | Agents can schedule and manage background tasks |
| **Skills System** | Load domain-specific capabilities (web research, code review, etc.) |
| **MCP Integration** | Connect to Model Context Protocol servers for extended tools |
| **Approval System** | Granular control over tool execution with auto-approval APIs |
| **Execution Hooks** | Intercept any pipeline point without modifying agent code |
| **Provider Failover** | Automatic health tracking and failover chains |

---

## Agent Variants

```python
from logicore import Agent, SmartAgent, CopilotAgent, MCPAgent

# Base Agent - Full control
agent = Agent(provider="ollama", model="qwen3.5:0.8b")

# SmartAgent - Reasoning-focused with auto-configuration
agent = SmartAgent(provider="ollama")

# CopilotAgent - Coding-focused with review/write capabilities
agent = CopilotAgent(provider="openai", model="gpt-4o")

# MCPAgent - Extended tools via Model Context Protocol
agent = MCPAgent(provider="ollama", mcp_config_path="mcp.json")
```

---

## Skills System

```python
# Load built-in skills
agent.load_skill("excel_operations")
agent.load_skill("pdf_operations")

# List available skills
skills = agent.list_available_skills()

# Unload a skill
agent.unload_skill("excel_operations")
```

---

## Tool Presets

```python
# Lightweight - Basic filesystem + web tools
agent = Agent(tools="lightweight")

# Smart - Full agentic toolkit
agent = Agent(tools="smart")

# Copilot - Code-focused tools
agent = Agent(tools="copilot")

# Full - All available tools
agent = Agent(tools="full")
```

---

## Documentation

| Level | Guide | Description |
|-------|-------|-------------|
| **Beginner** | [Installation](./docs/getting-started/installation.md) | Set up your environment |
| | [Quickstart](./docs/getting-started/quickstart.md) | Build your first agent |
| | [Basic Concepts](./docs/getting-started/concepts.md) | Core terminology |
| **Intermediate** | [Agent Guide](./docs/guides/agents.md) | Agent types and configuration |
| | [Tools Guide](./docs/guides/tools.md) | Custom tools and presets |
| | [Skills Guide](./docs/guides/skills.md) | Building and using skills |
| | [Memory Guide](./docs/guides/memory.md) | Persistent context |
| **Advanced** | [API Reference](./docs/api/agent.md) | Complete API docs |
| | [Architecture](./docs/guides/architecture.md) | System design |
| | [Contributing](./docs/contributing.md) | Development guide |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Your Application                        │
├─────────────────────────────────────────────────────────────┤
│                      Agent Layer                            │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐ │
│  │ Session │  │  Tools   │  │  Skills  │  │   Memory    │ │
│  │ Manager │  │ Registry │  │  Loader  │  │   Manager   │ │
│  └─────────┘  └──────────┘  └──────────┘  └─────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                   Execution Layer                           │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Tool      │  │    Chat      │  │     Input        │  │
│  │  Executor   │  │ Orchestrator │  │    Enricher      │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                   Context Layer                             │
│  ┌──────────────┐  ┌───────────────┐  ┌────────────────┐  │
│  │   Token      │  │   Context     │  │    Prompt       │  │
│  │  Estimator   │  │   Window Mgr  │  │   Assembler    │  │
│  └──────────────┘  └───────────────┘  └────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                   Provider Layer                            │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌──────┐ │
│  │ Ollama │  │ OpenAI │  │ Gemini │  │  Groq  │  │Azure │ │
│  └────────┘  └────────┘  └────────┘  └────────┘  └──────┘ │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           ModelAvailabilityService (Failover)        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Examples

| Example | Description |
|---------|-------------|
| [Basic Chat](./examples/sample_agent.py) | Simple agent with custom tools |
| [Streaming](./examples/streaming_chatbot.py) | Real-time token streaming |
| [Smart Agent](./examples/simple_runtime_chatbot.py) | Reasoning-focused agent |
| [Power Chatbot](./examples/power_chatbot.py) | Full-featured chatbot |
| [Advanced Runtime](./examples/advanced_runtime_agent.py) | Production runtime setup |

---

## Community

- **Discord**: [Join the server](https://discord.gg/Yz8yFzgQ)
- **GitHub**: [RudraModi360/Agentry](https://github.com/RudraModi360/Agentry)
- **PyPI**: [logicore](https://pypi.org/project/logicore/)
- **Issues**: [Report bugs](https://github.com/RudraModi360/Agentry/issues)

---

## Contributing

See [CONTRIBUTING.md](./docs/contributing.md) for development setup and guidelines.

---

## License

MIT License - see [LICENSE](./LICENSE) for details.

---

<p align="center">
    Built with ❤️ for multi-provider agentic workflows
</p>
