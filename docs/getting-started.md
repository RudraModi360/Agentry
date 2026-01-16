---
layout: page
title: Getting Started
nav_order: 2
description: "Installation guide and first steps with Agentry"
---

# Getting Started

This guide covers installation, prerequisites, and creating your first AI agent with Agentry.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Provider Setup](#provider-setup)
4. [Your First Agent](#your-first-agent)
5. [Using Different Providers](#using-different-providers)
6. [Interactive Interfaces](#interactive-interfaces)
7. [Custom System Prompt](#custom-system-prompt)
8. [CopilotAgent](#copilotagent-for-coding-tasks)
9. [Verifying Installation](#verifying-installation)
10. [Troubleshooting](#troubleshooting-common-issues)
11. [Next Steps](#next-steps)

---

## Prerequisites

Before installing Agentry, ensure you have the following:

| Requirement | Version | Notes |
|:------------|:--------|:------|
| Python | 3.11 or higher | Required for async features |
| pip or uv | Latest | Package manager |
| LLM Provider | See below | At least one provider configured |

### LLM Provider Options

| Provider | Type | API Key Required | Setup Difficulty |
|:---------|:-----|:-----------------|:-----------------|
| Ollama | Local | No | Easy |
| Groq | Cloud | Yes | Easy |
| Google Gemini | Cloud | Yes | Easy |
| Azure OpenAI | Cloud | Yes + Endpoint | Moderate |

---

## Installation

### Option 1: Install from PyPI (Recommended)

```bash
pip install agentry_community
```

### Option 2: Install from Source (Development)

```bash
# Clone the repository
git clone https://github.com/RudraModi360/Agentry.git
cd Agentry

# Create virtual environment (recommended)
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install in editable mode
pip install -e .
```

### Option 3: Using uv (Fast)

```bash
git clone https://github.com/RudraModi360/Agentry.git
cd Agentry
uv sync
```

---

## Provider Setup

### Ollama (Local LLM)

Ollama runs models locally on your machine, providing privacy and no API costs.

**Step 1: Install Ollama**

Download from [ollama.ai/download](https://ollama.ai/download) and follow the installation instructions for your operating system.

**Step 2: Pull a Model**

```bash
# Pull a model (examples)
ollama pull llama3.2:3b          # Smaller, faster
ollama pull llama3.2             # Default size
ollama pull codellama            # Optimized for code
```

**Step 3: Verify Ollama is Running**

```bash
ollama list
```

### Groq (Cloud LLM)

Groq provides ultra-fast inference via their LPU architecture.

**Step 1: Get API Key**

Visit [console.groq.com](https://console.groq.com/) and create an API key.

**Step 2: Configure Environment**

```bash
# Set environment variable
export GROQ_API_KEY="your-api-key-here"

# Or on Windows PowerShell
$env:GROQ_API_KEY="your-api-key-here"
```

### Google Gemini (Cloud LLM)

**Step 1: Get API Key**

Visit [ai.google.dev](https://ai.google.dev/) and generate an API key.

**Step 2: Configure Environment**

```bash
export GEMINI_API_KEY="your-api-key-here"
```

### Azure OpenAI

**Step 1: Create Azure OpenAI Resource**

Follow the Azure documentation to create an OpenAI resource and deploy a model.

**Step 2: Configure Environment**

```bash
export AZURE_API_KEY="your-api-key-here"
export AZURE_ENDPOINT="https://your-resource.openai.azure.com"
```

---

## Your First Agent

Create a file named `my_first_agent.py`:

```python
import asyncio
from agentry import Agent

async def main():
    # Initialize agent with Ollama provider
    agent = Agent(llm="ollama", model="llama3.2:3b")
    
    # Load built-in tools (filesystem, web, execution)
    agent.load_default_tools()
    
    # Send a message and get response
    response = await agent.chat("Hello! What can you help me with?")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
```

Run the agent:

```bash
python my_first_agent.py
```

---

## Using Different Providers

### Groq Provider

```python
from agentry import Agent

agent = Agent(
    llm="groq",
    model="llama-3.3-70b-versatile",
    api_key="your-groq-api-key"  # Or use environment variable
)
agent.load_default_tools()
```

### Gemini Provider

```python
from agentry import Agent

agent = Agent(
    llm="gemini",
    model="gemini-2.0-flash",
    api_key="your-gemini-api-key"
)
agent.load_default_tools()
```

### Azure Provider

```python
from agentry import Agent

agent = Agent(
    llm="azure",
    model="gpt-4",
    api_key="your-azure-api-key",
    endpoint="https://your-resource.openai.azure.com"
)
agent.load_default_tools()
```

---

## Interactive Interfaces

### Command-Line Interface (CLI)

Launch the terminal-based interface:

```bash
agentry_cli
```

CLI options:

| Option | Short | Description |
|:-------|:------|:------------|
| `--provider` | `-p` | LLM provider: ollama, groq, gemini, azure |
| `--model` | `-m` | Model name |
| `--agent` | `-a` | Agent type: default, smart, copilot |
| `--session` | `-s` | Resume a specific session |
| `--debug` | `-d` | Enable debug output |

**Example:**

```bash
agentry_cli -p groq -m llama-3.3-70b-versatile
```

### Web Interface (GUI)

Launch the browser-based interface:

```bash
agentry_gui
```

Then open [http://localhost:8000](http://localhost:8000) in your browser.

---

## Custom System Prompt

You can customize the agent's behavior with a system message:

```python
from agentry import Agent

agent = Agent(
    llm="ollama",
    model="llama3.2",
    system_message="You are a Python programming tutor. Explain concepts clearly with examples.",
    role="general"
)
agent.load_default_tools()
```

---

## CopilotAgent for Coding Tasks

Agentry includes a specialized agent for coding tasks:

```python
from agentry import CopilotAgent

copilot = CopilotAgent(llm="ollama", model="codellama")

# Coding task
response = await copilot.chat("Create a function to calculate factorial")

# General chat (uses separate context)
response = await copilot.general_chat("Explain recursion")
```

---

## Verifying Installation

Run this script to verify your installation is working:

```python
import asyncio
from agentry import Agent

async def verify():
    try:
        agent = Agent(llm="ollama", model="llama3.2:3b")
        agent.load_default_tools()
        
        response = await agent.chat("Say 'Installation successful!' and nothing else.")
        print(f"Agent Response: {response}")
        print("\nAgentry is installed and working correctly.")
    except Exception as e:
        print(f"Error: {e}")
        print("\nPlease check your installation and provider configuration.")

if __name__ == "__main__":
    asyncio.run(verify())
```

---

## Troubleshooting Common Issues

### "Connection refused" Error

Ollama server is not running:

```bash
ollama serve
```

### "Model not found" Error

Pull the model first:

```bash
ollama pull llama3.2:3b
```

### Import Errors

Ensure you are in the correct directory and dependencies are installed:

```bash
cd Agentry
pip install -e .
```

For more issues, see the [Troubleshooting Guide](troubleshooting).

---

## Next Steps

| Topic | Description |
|:------|:------------|
| [Core Concepts](core-concepts) | Understanding the agent loop, tools, and providers |
| [API Reference](api-reference) | Complete API documentation |
| [Custom Tools](custom-tools) | Creating your own tools |
| [Examples](examples) | Practical code examples |
