---
title: Getting Started
description: Installation and quickstart guides for Logicore
---

# Getting Started

Welcome to Logicore! This section will help you set up your environment and build your first AI agent.

## Prerequisites

- Python 3.10 or higher
- An LLM provider (Ollama for local, or API key for cloud providers)

## Installation

```bash
pip install logicore
```

For development with all extras:

```bash
pip install logicore[dev]
```

## Quick Links

| Guide | Description | Time |
|-------|-------------|------|
| [Installation](./installation.md) | Detailed setup instructions | 2 min |
| [Provider Setup](./providers.md) | Configure LLM providers | 5 min |
| [Quickstart](./quickstart.md) | Build your first agent | 5 min |
| [Basic Concepts](./concepts.md) | Core terminology | 10 min |

## Your First Agent

```python
import asyncio
from logicore import Agent

async def main():
    # Create an agent with Ollama (local)
    agent = Agent(
        provider="ollama",
        model="qwen3.5:0.8b",
        role="Assistant"
    )
    
    # Chat with the agent
    response = await agent.chat("Hello! What can you do?")
    print(response["content"])

asyncio.run(main())
```

## Next Steps

1. [Installation Guide](./installation.md) - Detailed setup for each provider
2. [Quickstart Tutorial](./quickstart.md) - Build a tool-enabled agent
3. [Core Concepts](./concepts.md) - Understand the architecture
4. [Agent Guide](../guides/agents.md) - Deep dive into agent types
