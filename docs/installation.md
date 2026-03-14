# Installation Guide

Get Logicore up and running on your machine in 2 minutes.

## Prerequisites

- **Python 3.8+** — Check with `python --version`
- **pip** — Python package manager (comes with Python)
- **An LLM** — Pick local (Ollama) or cloud (OpenAI, Groq, Gemini, Azure, Anthropic)

---

## Step 1: Install Logicore Core

### Basic Installation

```bash
pip install logicore
```

This installs Logicore with support for local models via Ollama.

### With Specific Provider

Choose what you need:

```bash
# Google Gemini
pip install logicore[gemini]

# Groq (fast & cheap)
pip install logicore[groq]

# Local models with Ollama  
pip install logicore[ollama]

# Azure OpenAI
pip install logicore[azure]

# Anthropic (Claude)
pip install logicore[anthropic]

# OpenAI (GPT-4, etc)
pip install logicore[openai]

# Everything (all providers + features)
pip install logicore[all]
```

---

## Step 2: Set Up Your LLM Provider

### Option A: Local (Free, No API Key) — Recommended for Beginners

Use **Ollama** for completely free, privacy-first inference.

```bash
# 1. Download Ollama from https://ollama.ai
# 2. Install and open the application
# 3. Run a model in your terminal
ollama run qwen3.5:0.8b
# This downloads a small model (~900MB) and starts it

# 4. Logicore auto-detects it. You're done!
```

Then in Python:

```python
from logicore import Agent

# Automatically finds Ollama on localhost:11434
agent = Agent()  # No config needed!
response = agent.chat("Hello!")
print(response)
```

### Option B: OpenAI (Paid, Fastest)

```bash
# 1. Get API key from https://platform.openai.com
# 2. Set environment variable
export OPENAI_API_KEY=sk-...

# Windows PowerShell:
$env:OPENAI_API_KEY="sk-..."
```

Then in Python:

```python
from logicore import Agent
from logicore.providers import OpenAIProvider

agent = Agent(provider=OpenAIProvider(model="gpt-4"))
response = agent.chat("Explain quantum computing")
print(response)
```

### Option C: Groq (Fast & Affordable)

```bash
# 1. Get API key from https://console.groq.com
# 2. Set environment variable
export GROQ_API_KEY=gsk_...

# Windows PowerShell:
$env:GROQ_API_KEY="gsk_..."
```

Then in Python:

```python
from logicore import Agent
from logicore.providers import GroqProvider

agent = Agent(provider=GroqProvider(model="llama-3.3-70b-versatile"))
response = agent.chat("Hello!")
print(response)
```

### Option D: Google Gemini

```bash
# 1. Get API key from https://ai.google.dev
# 2. Set environment variable
export GOOGLE_API_KEY=...

# Windows PowerShell:
$env:GOOGLE_API_KEY="..."
```

Then in Python:

```python
from logicore import Agent
from logicore.providers import GeminiProvider

agent = Agent(provider=GeminiProvider(model="gemini-2.0-flash"))
response = agent.chat("Hello!")
print(response)
```

### Option E: Azure OpenAI

```bash
# 1. Get keys from Azure Portal
# 2. Set environment variables
export AZURE_OPENAI_KEY=...
export AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
export AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Windows PowerShell:
$env:AZURE_OPENAI_KEY="..."
$env:AZURE_OPENAI_ENDPOINT="https://..."
$env:AZURE_OPENAI_API_VERSION="2024-02-15-preview"
```

Then in Python:

```python
from logicore import Agent
from logicore.providers import AzureOpenAIProvider

agent = Agent(provider=AzureOpenAIProvider(model="gpt-4"))
response = agent.chat("Hello!")
print(response)
```

### Option F: Anthropic (Claude)

```bash
# 1. Get API key from https://console.anthropic.com
# 2. Set environment variable
export ANTHROPIC_API_KEY=sk-ant-...

# Windows PowerShell:
$env:ANTHROPIC_API_KEY="sk-ant-..."
```

Then in Python:

```python
from logicore import Agent
from logicore.providers import AnthropicProvider

agent = Agent(provider=AnthropicProvider(model="claude-3-5-sonnet-20241022"))
response = agent.chat("Hello!")
print(response)
```

---

## Step 3: Verify Installation

Create a file `test_logicore.py`:

```python
from logicore import Agent

# Test with default provider (Ollama if running, else error)
agent = Agent()
response = agent.chat("Say 'Logicore is working!' if you can read this")
print(response)
```

Run it:

```bash
python test_logicore.py
```

**Expected output:**
```
Logicore is working!
```

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'logicore'`
You haven't installed Logicore yet.
```bash
pip install logicore
```

### `ConnectionError: Could not connect to provider`
Your LLM provider isn't running or configured.
- **Ollama**: Did you run `ollama run qwen3.5:0.8b`?
- **OpenAI**: Is your `OPENAI_API_KEY` set? Check with `echo $OPENAI_API_KEY`
- **Groq**: Is your `GROQ_API_KEY` set?

### `No provider found`
Logicore couldn't auto-detect any provider. Explicitly set one:
```python
from logicore import Agent
from logicore.providers import OllamaProvider

agent = Agent(provider=OllamaProvider(model="llama3.2"))
```

### `Model not found: qwen3.5:0.8b`
Ollama model didn't download. Run manually:
```bash
ollama run qwen3.5:0.8b
```

---

## Optional: Enable Advanced Features

### Install with Vision Support

```bash
pip install logicore[vision]
```

Then use image understanding:

```python
from logicore import Agent

agent = Agent()
response = agent.chat("Describe this image", image_path="photo.jpg")
```

### Install with MCP Support

```bash
pip install logicore[mcp]
```

Then connect MCP servers:

```python
from logicore import MCPAgent

agent = MCPAgent(mcp_config="mcp.json")
```

### Install with Telemetry

```bash
pip install logicore[telemetry]
```

Then track token usage:

```python
agent = Agent(telemetry=True)
response = agent.chat("Hello")
print(agent.telemetry)  # See token counts, latency, etc.
```

---

## Next Steps

1. **[Quick Start](quickstart.md)** — Build your first agent
2. **[Core Concepts](concepts/agents.md)** — Learn how Logicore works
3. **[Guides](../guides/)** — Real-world patterns and examples

---

## Getting Help

- 💬 **Discord** — [Join community](https://discord.gg/logicore)
- 🐛 **Issues** — [GitHub Issues](https://github.com/RudraModi360/Logicore/issues)
- 📖 **FAQ** — Coming soon
