---
title: Installation
description: Detailed installation guide for Logicore
---

# Installation

## System Requirements

- **Python**: 3.10, 3.11, 3.12, or 3.13
- **OS**: Windows, macOS, or Linux
- **Memory**: 4GB+ RAM recommended (for local models)

## Basic Installation

```bash
pip install logicore
```

## Provider-Specific Setup

### Ollama (Local, Free)

1. Install Ollama: https://ollama.com
2. Pull a model:
   ```bash
   ollama pull qwen3.5:0.8b
   ```
3. No API key needed - runs entirely on your machine

```python
from logicore import Agent

agent = Agent(provider="ollama", model="qwen3.5:0.8b")
```

### OpenAI (Cloud)

1. Get API key from: https://platform.openai.com
2. Set environment variable:
   ```bash
   export OPENAI_API_KEY="your-key-here"
   ```

```python
from logicore import Agent

agent = Agent(provider="openai", model="gpt-4o")
```

### Google Gemini

1. Get API key from: https://aistudio.google.com
2. Set environment variable:
   ```bash
   export GEMINI_API_KEY="your-key-here"
   ```

```python
from logicore import Agent

agent = Agent(provider="gemini", model="gemini-2.0-flash")
```

### Groq

1. Get API key from: https://console.groq.com
2. Set environment variable:
   ```bash
   export GROQ_API_KEY="your-key-here"
   ```

```python
from logicore import Agent

agent = Agent(provider="groq", model="llama-3.3-70b-versatile")
```

### Azure OpenAI

1. Set up Azure OpenAI resource in Azure Portal
2. Set environment variables:
   ```bash
   export AZURE_OPENAI_API_KEY="your-key-here"
   export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
   export AZURE_OPENAI_API_VERSION="2024-02-01"
   ```

```python
from logicore import Agent

agent = Agent(
    provider="azure",
    model="gpt-4o",
    endpoint="https://your-resource.openai.azure.com/",
    api_key="your-key-here"
)
```

## Environment Variables

Create a `.env` file in your project root:

```env
# Ollama (no key needed)
OLLAMA_BASE_URL=http://localhost:11434

# OpenAI
OPENAI_API_KEY=sk-...

# Gemini
GEMINI_API_KEY=AI...

# Groq
GROQ_API_KEY=gsk_...

# Azure
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://...
```

## Verifying Installation

```python
from logicore import Agent
import asyncio

async def test():
    agent = Agent(provider="ollama", model="qwen3.5:0.8b")
    response = await agent.chat("Say hello")
    print(response["content"])

asyncio.run(test())
```

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'logicore'` | Run `pip install logicore` |
| `Connection refused` (Ollama) | Ensure Ollama is running: `ollama serve` |
| `Invalid API key` | Check environment variable is set correctly |
| `Model not found` | Pull the model: `ollama pull model-name` |

### Getting Help

- [GitHub Issues](https://github.com/RudraModi360/Agentry/issues)
- [Discord Community](https://discord.gg/Yz8yFzgQ)
