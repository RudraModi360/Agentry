---
title: Memory Guide
description: Persistent context and knowledge management
---

# Memory Guide

Logicore's memory system enables agents to remember context across sessions. This guide covers memory configuration, usage, and management.

## Overview

The memory system provides:

- **Persistent Storage**: Remember across sessions
- **Semantic Search**: Find relevant memories
- **Automatic Extraction**: Extract facts from conversations
- **Domain Organization**: Categorize memories by type

## Enabling Memory

```python
agent = Agent(
    provider="ollama",
    memory=True,  # Enable memory
    memory_dir="~/.logicore/memory"  # Optional: custom path
)
```

## Memory Domains

| Domain | Description | Examples |
|--------|-------------|----------|
| `IDENTITY` | User identity | Name, role, preferences |
| `PREFERENCES` | User preferences | Favorite colors, settings |
| `RELATIONSHIPS` | People connections | Colleagues, family |
| `KNOWLEDGE` | Facts and information | Learned concepts |
| `DOMAIN` | Domain-specific | Project details, work context |
| `ADDITIONAL_LEARNING` | Learned patterns | User behavior patterns |
| `OPERATIONAL` | Operational data | Session patterns, errors |

## Using Memory

### Automatic Memory

When memory is enabled, agents automatically:

1. **Extract Facts**: Important information from conversations
2. **Store Memories**: Save to persistent storage
3. **Retrieve Relevant**: Load relevant memories before responses
4. **Update**: Modify existing memories as needed

```python
agent = Agent(provider="ollama", memory=True)

# First conversation
await agent.chat("My name is Alice")
await agent.chat("I work at TechCorp")

# Later conversation (different session)
await agent.chat("What's my name?")
# Agent remembers: "Your name is Alice"

await agent.chat("Where do I work?")
# Agent remembers: "You work at TechCorp"
```

### Manual Memory Operations

```python
# Submit conversation for extraction
await agent.memory.submit_for_extraction(conversation)

# Reset retrieval state
agent.memory.reset_session()

# Get memory statistics
stats = agent.memory.get_stats()
```

## Memory Types

### Facts

Concrete information:

```python
# Automatically extracted
"My name is Alice"
"I work at TechCorp"
"The project deadline is March 15"
```

### Guidelines

Rules and preferences:

```python
# Automatically extracted
"I prefer dark mode"
"Always use TypeScript"
"Never schedule meetings before 10 AM"
```

### Context

Situational information:

```python
# Automatically extracted
"We're working on the auth module"
"The client prefers React"
"The database is PostgreSQL"
```

### Lessons

Learned patterns:

```python
# Automatically extracted
"When I say 'quick fix', I mean minimal changes"
"I prefer detailed code reviews"
```

## Memory Storage

### File-Based Storage

Default storage uses YAML files:

```
~/.logicore/memory/
├── identity/
│   ├── alice_name.yaml
│   └── alice_role.yaml
├── preferences/
│   └── dark_mode.yaml
├── knowledge/
│   └── project_deadline.yaml
└── MEMORY.md  # Index file
```

### Memory File Format

```yaml
---
domain: IDENTITY
kind: FACT
stability: STABLE
confidence: 0.95
created_at: 2025-01-15T10:30:00Z
updated_at: 2025-01-15T10:30:00Z
tags:
  - name
  - identity
---

# User Name

The user's name is Alice.
```

## Memory Manager

### Configuration

```python
from logicore.memory import MemoryManager

memory = MemoryManager(
    memory_dir="~/.logicore/memory",
    llm_provider="ollama",
    llm_model="qwen3.5:0.8b",
    enabled=True,
    throttle_interval=30,  # Seconds between extractions
    transcript_window=50    # Max messages for extraction
)
```

### Starting Memory

```python
# Start background workers
await memory.start()

# Use memory
agent = Agent(provider="ollama", memory=memory)

# Stop when done
await memory.stop()
```

### Memory Prompt Section

Memory automatically injects relevant context into the system prompt:

```python
# Get memory section for prompt
section = await memory.get_memory_prompt_section()

# Inject before user message
messages = [{"role": "system", "content": section}] + user_messages
```

## Semantic Search

### Querying Memories

```python
from logicore.memory.retrieval import MemoryRetriever

retriever = MemoryRetriever(memory_dir="~/.logicore/memory")

# Search by query
results = await retriever.search("What is Alice's role?")

# Search by domain
results = await retriever.search(domain="IDENTITY")

# Search by tags
results = await retriever.search(tags=["name", "identity"])
```

### Scoring

Memories are scored by:

- **Relevance**: Semantic similarity to query
- **Recency**: How recently accessed
- **Stability**: Memory stability level
- **Confidence**: Extraction confidence

## Memory Extraction

### Background Worker

```python
# Extraction happens in background
await memory.submit_for_extraction(conversation)

# Worker extracts facts, guidelines, etc.
# Stores to memory files
# Updates index
```

### Extraction Configuration

```python
memory = MemoryManager(
    throttle_interval=30,  # Min seconds between extractions
    transcript_window=50   # Max messages to process
)
```

## Memory Consolidation

### Merging Duplicate Memories

```python
# Consolidation merges similar memories
# Happens periodically in background
# Reduces memory clutter
```

### Stability Levels

| Level | Half-Life | Example |
|-------|-----------|---------|
| `STABLE` | 365 days | User name, role |
| `EVOLVING` | 90 days | Project details |
| `VOLATILE` | 7 days | Current task |
| `EPHEMERAL` | 1 day | Temporary context |

## Best Practices

1. **Enable Early**: Enable memory from the start
2. **Meaningful IDs**: Use descriptive session IDs
3. **Reset Sessions**: Reset when context changes
4. **Monitor Stats**: Check memory stats periodically
5. **Consolidate**: Allow consolidation to run

## Next Steps

- [Memory API Reference](../api/memory.md)
- [Memory Examples](../examples/memory/)
- [Architecture](./architecture.md)
