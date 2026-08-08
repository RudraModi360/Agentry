---
title: Provider Setup
description: Configure LLM providers for Logicore
---

# Provider Setup

Logicore supports multiple LLM providers. This guide covers setup and configuration for each.

## Quick Comparison

| Provider | Type | Cost | Latency | Best For |
|----------|------|------|---------|----------|
| Ollama | Local | Free | Low | Development, privacy |
| OpenAI | Cloud | Per-token | Medium | Production, quality |
| Gemini | Cloud | Per-token | Medium | Multi-modal, speed |
| Groq | Cloud | Per-token | Low | Fast inference |
| Azure | Enterprise | Per-token | Medium | Compliance, scale |

---

## Ollama (Local)

### Installation

1. Download from https://ollama.com
2. Install and start the service:

```bash
# macOS/Linux
ollama serve

# Windows
# Ollama runs as a service after installation
```

### Pull a Model

```bash
# Small and fast (recommended for starting)
ollama pull qwen3.5:0.8b

# Better quality
ollama pull qwen3.5:4b

# Best quality (requires more RAM)
ollama pull qwen3.5:8b

# Other popular models
ollama pull llama3.2:3b
ollama pull mistral:7b
ollama pull codellama:7b
```

### Usage

```python
from logicore import Agent

# Basic usage (defaults to localhost:11434)
agent = Agent(
    provider="ollama",
    model="qwen3.5:0.8b",
    role="Assistant"
)

# With custom endpoint
agent = Agent(
    provider="ollama",
    model="qwen3.5:0.8b",
    endpoint="http://localhost:11434"
)

# With Ollama Cloud (remote server)
agent = Agent(
    provider="ollama",
    model="qwen3.5:0.8b",
    endpoint="https://your-ollama-server.example.com"
)
```

### Ollama Cloud Setup

For remote Ollama servers (self-hosted or cloud VMs):

1. **Set up remote server:**
   ```bash
   # On remote server
   ollama serve --host 0.0.0.0 --port 11434
   ```

2. **Configure firewall/security:**
   - Open port 11434
   - Use SSL/TLS for production (via reverse proxy)

3. **Connect from Logicore:**
   ```python
   agent = Agent(
       provider="ollama",
       model="qwen3.5:0.8b",
       endpoint="https://your-server.example.com"
   )
   ```

### Environment Variables

```env
OLLAMA_BASE_URL=http://localhost:11434
```

### Available Models

| Model | Size | RAM Required | Quality |
|-------|------|--------------|---------|
| qwen3.5:0.8b | 0.8B | 1GB | Good |
| qwen3.5:4b | 4B | 5GB | Better |
| qwen3.5:8b | 8B | 9GB | Best |
| llama3.2:3b | 3B | 4GB | Good |
| mistral:7b | 7B | 8GB | Better |
| codellama:7b | 7B | 8GB | Code-focused |

---

## OpenAI

### Setup

1. Get API key from https://platform.openai.com
2. Set environment variable:

```bash
export OPENAI_API_KEY="sk-..."
```

### Usage

```python
from logicore import Agent

# GPT-4o (recommended)
agent = Agent(
    provider="openai",
    model="gpt-4o",
    api_key="sk-..."  # Or use env var
)

# GPT-4o Mini (faster, cheaper)
agent = Agent(
    provider="openai",
    model="gpt-4o-mini"
)

# GPT-4 Turbo
agent = Agent(
    provider="openai",
    model="gpt-4-turbo"
)
```

### Environment Variables

```env
OPENAI_API_KEY=sk-...
```

### Available Models

| Model | Context | Best For |
|-------|---------|----------|
| gpt-4o | 128K | General, high quality |
| gpt-4o-mini | 128K | Fast, cost-effective |
| gpt-4-turbo | 128K | Complex reasoning |
| gpt-3.5-turbo | 16K | Simple tasks |

---

## Google Gemini

### Setup

1. Get API key from https://aistudio.google.com
2. Set environment variable:

```bash
export GEMINI_API_KEY="AI..."
```

### Usage

```python
from logicore import Agent

# Gemini 2.0 Flash (recommended)
agent = Agent(
    provider="gemini",
    model="gemini-2.0-flash",
    api_key="AI..."  # Or use env var
)

# Gemini 1.5 Pro
agent = Agent(
    provider="gemini",
    model="gemini-1.5-pro"
)

# Gemini 1.5 Flash
agent = Agent(
    provider="gemini",
    model="gemini-1.5-flash"
)
```

### Environment Variables

```env
GEMINI_API_KEY=AI...
```

### Available Models

| Model | Context | Best For |
|-------|---------|----------|
| gemini-2.0-flash | 1M | Fast, multi-modal |
| gemini-1.5-pro | 2M | Complex tasks |
| gemini-1.5-flash | 1M | Fast, cost-effective |

---

## Groq

### Setup

1. Get API key from https://console.groq.com
2. Set environment variable:

```bash
export GROQ_API_KEY="gsk_..."
```

### Usage

```python
from logicore import Agent

# Llama 3.3 70B (recommended)
agent = Agent(
    provider="groq",
    model="llama-3.3-70b-versatile",
    api_key="gsk_..."  # Or use env var
)

# Mixtral 8x7B
agent = Agent(
    provider="groq",
    model="mixtral-8x7b-32768"
)

# Gemma 2 9B
agent = Agent(
    provider="groq",
    model="gemma2-9b-it"
)
```

### Environment Variables

```env
GROQ_API_KEY=gsk_...
```

### Available Models

| Model | Context | Best For |
|-------|---------|----------|
| llama-3.3-70b-versatile | 128K | General, high quality |
| mixtral-8x7b-32768 | 32K | Fast, good quality |
| gemma2-9b-it | 8K | Lightweight tasks |

### Why Groq?

- **Fastest inference** in the industry
- **Low latency** for real-time applications
- **Free tier** available for development

---

## Azure OpenAI

### Setup

1. Create Azure OpenAI resource in Azure Portal
2. Deploy a model
3. Set environment variables:

```bash
export AZURE_OPENAI_API_KEY="your-key-here"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_VERSION="2024-02-01"
```

### Usage

```python
from logicore import Agent

# With environment variables
agent = Agent(
    provider="azure",
    model="gpt-4o"  # Must match deployed model name
)

# With explicit configuration
agent = Agent(
    provider="azure",
    model="gpt-4o",
    api_key="your-key-here",
    endpoint="https://your-resource.openai.azure.com/"
)
```

### Environment Variables

```env
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-01
```

### When to Use Azure

- Enterprise compliance requirements
- Existing Azure infrastructure
- Data residency requirements
- VNet integration needs

---

## Provider Failover

Configure automatic failover when a provider fails:

```python
from logicore import Agent
from logicore.providers import ModelAvailabilityService
from logicore.providers import OpenAIProvider, GroqProvider, OllamaProvider

# Create availability service
availability = ModelAvailabilityService()

# Register providers with priorities
availability.register_provider("openai", OpenAIProvider(model="gpt-4o"), priority=1)
availability.register_provider("groq", GroqProvider(model="llama-3.3-70b"), priority=2)
availability.register_provider("ollama", OllamaProvider(model="qwen3.5:0.8b"), priority=3)

# Get available provider
provider = availability.get_available_provider()

# Create agent with failover
agent = Agent(provider=provider)
```

### How It Works

1. Tries OpenAI first (priority 1)
2. If OpenAI fails, tries Groq (priority 2)
3. If Groq fails, tries Ollama (priority 3)

---

## Provider Selection Guide

### For Development

```python
# Use Ollama (free, local)
agent = Agent(provider="ollama", model="qwen3.5:0.8b")
```

### For Production (Quality)

```python
# Use OpenAI or Gemini
agent = Agent(provider="openai", model="gpt-4o")
agent = Agent(provider="gemini", model="gemini-2.0-flash")
```

### For Production (Speed)

```python
# Use Groq
agent = Agent(provider="groq", model="llama-3.3-70b-versatile")
```

### For Enterprise

```python
# Use Azure
agent = Agent(provider="azure", model="gpt-4o")
```

### For Privacy

```python
# Use Ollama (data stays local)
agent = Agent(provider="ollama", model="qwen3.5:8b")
```

---

## Testing Providers

```python
import asyncio
from logicore import Agent

async def test_provider(provider, model):
    agent = Agent(provider=provider, model=model)
    response = await agent.chat("Say hello in one word")
    print(f"{provider}: {response['content']}")

async def main():
    # Test each configured provider
    await test_provider("ollama", "qwen3.5:0.8b")
    # await test_provider("openai", "gpt-4o")
    # await test_provider("gemini", "gemini-2.0-flash")
    # await test_provider("groq", "llama-3.3-70b-versatile")

asyncio.run(main())
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `Connection refused` (Ollama) | Run `ollama serve` |
| `Invalid API key` | Check environment variable |
| `Model not found` | Pull model: `ollama pull model-name` |
| `Rate limited` | Wait or switch provider |
| `Timeout` | Check network, increase timeout |

### Debug Mode

```python
agent = Agent(
    provider="ollama",
    model="qwen3.5:0.8b",
    debug=True  # Enable detailed logging
)
```

---

## Next Steps

- [Quickstart](./quickstart.md) - Build your first agent
- [Agent Guide](../guides/agents.md) - Deep dive into agent configuration
- [Architecture](../guides/architecture.md) - System design
