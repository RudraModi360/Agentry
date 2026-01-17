---
layout: default
title: Home
nav_order: 1
permalink: /
---

# Agentry Documentation

A powerful, modular AI agent framework for Python.
{: .fs-6 .fw-300 }

[Get Started](getting-started){: .btn .btn-primary .fs-5 .mb-4 .mb-md-0 .mr-2 }
[View on GitHub](https://github.com/RudraModi360/Agentry){: .btn .fs-5 .mb-4 .mb-md-0 }

---

## What is Agentry?

Agentry is a privacy-focused AI agent framework that provides a unified interface for building AI agents that can reason, use tools, and maintain conversation context.

### Key Features

- **Multi-Provider LLM Support** - Ollama, Groq, Google Gemini, Azure OpenAI
- **Built-in Tools** - Filesystem, web search, code execution, documents
- **MCP Integration** - Connect to external tool servers
- **Session Management** - Automatic persistence
- **Custom Tools** - Register Python functions as tools

---

## Tested Models

Agentry has been tested with various models across different providers:

| Provider | Model | Type |
|:---------|:------|:-----|
| **Ollama** | `gpt-oss:20b:cloud` | Cloud-optimized |
| **Ollama** | `glm-4.5:cloud` | Cloud-optimized |
| **Azure** | `claude-opus:4.5` | Enterprise |
| **Groq** | `llama-3.3-70b-versatile` | High performance |
| **Gemini** | `gemini-2.0-flash` | Multimodal |

---

## Quick Installation

```bash
pip install agentry_community
```

---

## Quick Start

```python
import asyncio
from agentry import Agent

async def main():
    agent = Agent(llm="ollama", model="gpt-oss:20b:cloud")
    agent.load_default_tools()
    
    response = await agent.chat("Hello!")
    print(response)

asyncio.run(main())
```

---

## Documentation Sections

| Section | Description |
|:--------|:------------|
| [Getting Started](getting-started) | Installation and first steps |
| [Core Concepts](core-concepts) | Architecture and fundamentals |
| [API Reference](api-reference) | Complete API documentation |
| [Custom Tools](custom-tools) | Creating your own tools |
| [MCP Integration](mcp-integration) | External tool servers |
| [Examples](examples) | Practical code examples |
| [Troubleshooting](troubleshooting) | Common issues |

---

## Support

- [GitHub Issues](https://github.com/RudraModi360/Agentry/issues)
- [Discussions](https://github.com/RudraModi360/Agentry/discussions)
- Email: rudramodi9560@gmail.com
