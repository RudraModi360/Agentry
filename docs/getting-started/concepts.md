---
title: Basic Concepts
description: Core terminology and architecture overview
---

# Basic Concepts

Understanding Logicore's core building blocks.

## Core Components

### Agent

The central orchestrator that manages conversations, tools, and memory.

```python
from logicore import Agent

agent = Agent(
    provider="ollama",    # LLM provider
    model="qwen3.5:0.8b", # Model name
    role="Assistant"      # Agent persona
)
```

**Key Properties:**
- `provider` - Which LLM to use (ollama, openai, gemini, groq, azure)
- `model` - Specific model identifier
- `role` - Agent's persona and behavior
- `tools` - Available tools for the agent
- `skills` - Loaded skill packages

### Tools

Python functions that agents can call to interact with the world.

```python
def get_weather(city: str) -> str:
    """Get current weather for a city."""
    return f"Sunny, 72°F in {city}"

# Tool is auto-registered via type hints + docstring
agent = Agent(tools=[get_weather])
```

**Tool Requirements:**
- Type hints for parameters (for schema generation)
- Docstring with description (for LLM understanding)
- Return type annotation

### Skills

Reusable capability packages that bundle tools, instructions, and examples.

```python
# Load a skill
agent.load_skill("excel_operations")

# Skills provide:
# - Tool schemas
# - Usage instructions
# - Example prompts
# - Validation rules
```

### Sessions

Conversation state management for multi-turn interactions.

```python
# Create a session
session = agent.create_session("my-session")

# Continue conversation in same session
response1 = await agent.chat("My name is Alice", session_id="my-session")
response2 = await agent.chat("What's my name?", session_id="my-session")
# Agent remembers: "Your name is Alice"
```

### Memory

Persistent knowledge storage across sessions.

```python
agent = Agent(
    provider="ollama",
    memory=True  # Enable persistent memory
)

# Memory automatically stores:
# - User preferences
# - Important facts
# - Learned patterns
```

### Providers

LLM backends that power agent reasoning.

| Provider | Type | Use Case |
|----------|------|----------|
| Ollama | Local | Development, privacy |
| OpenAI | Cloud | Production, quality |
| Gemini | Cloud | Multi-modal, speed |
| Groq | Cloud | Fast inference |
| Azure | Enterprise | Compliance, scale |

### Context

The conversation history and system prompt sent to the LLM.

```
┌─────────────────────────────────────┐
│           System Prompt             │
│         (Agent persona)             │
├─────────────────────────────────────┤
│           Memory Context            │
│       (Relevant memories)           │
├─────────────────────────────────────┤
│         Conversation History        │
│    (Previous user/assistant msgs)   │
├─────────────────────────────────────┤
│           Current Message           │
│       (User's latest input)         │
└─────────────────────────────────────┘
```

## Data Flow

```
User Input
    │
    ▼
┌─────────────────┐
│  Input Enricher │ ← Adds context, references
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Context Manager │ ← Manages token budget
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   LLM Provider  │ ← Generates response
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Tool Executor  │ ← Runs any tool calls
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Chat Orchestrator│ ← Manages conversation loop
└────────┬────────┘
         │
         ▼
    Response
```

## Configuration

### Environment Variables

```env
# Provider API Keys
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AI...
GROQ_API_KEY=gsk_...

# Ollama (optional)
OLLAMA_BASE_URL=http://localhost:11434
```

### Agent Configuration

```python
agent = Agent(
    # Provider
    provider="ollama",
    model="qwen3.5:0.8b",
    
    # Behavior
    role="Assistant",
    system_prompt="You are a helpful assistant.",
    
    # Tools
    tools=["smart"],  # Preset
    max_iterations=40,
    
    # Memory
    memory=True,
    
    # Debugging
    debug=True,
    telemetry=True
)
```

## Terminology

| Term | Definition |
|------|------------|
| **Provider** | LLM backend (Ollama, OpenAI, etc.) |
| **Tool** | Python function callable by the agent |
| **Skill** | Reusable capability package |
| **Session** | Conversation state container |
| **Memory** | Persistent knowledge storage |
| **Context** | Messages sent to the LLM |
| **Token** | Unit of text (word/subword) |
| **Streaming** | Real-time token delivery |
| **Hook** | Pipeline interception point |
| **MCP** | Model Context Protocol server |

## Next Steps

- [Agent Guide](../guides/agents.md) - Deep dive into agent types
- [Tools Guide](../guides/tools.md) - Create custom tools
- [Skills Guide](../guides/skills.md) - Build skill packages
- [Architecture](../guides/architecture.md) - System design details
