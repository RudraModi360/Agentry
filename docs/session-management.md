---
layout: page
title: Session Management
nav_order: 7
description: "Working with persistent sessions and conversation history"
---

# Session Management

Complete guide to session management in Agentry.

## Table of Contents

1. [Overview](#overview)
2. [Basic Usage](#basic-usage)
3. [Session Structure](#session-structure)
4. [Interactive Mode](#interactive-mode)
5. [Session Files](#session-files)
6. [Multi-Session Management](#multi-session-management)
7. [Advanced Features](#advanced-features)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)
10. [Session Object Reference](#session-object-reference)
11. [SessionManager Reference](#sessionmanager-reference)
12. [Next Steps](#next-steps)

---

## Overview

Sessions maintain conversation context across multiple interactions. Agentry provides:

- Automatic persistence to `.toon` format
- Multi-session support
- Session switching
- History preservation
- Metadata tracking

![Session Management](assets/images/session-management.png)

---

## Basic Usage

### Creating and Using Sessions

```python
from agentry import Agent

agent = Agent(llm="ollama")
agent.load_default_tools()

# Chat in default session
await agent.chat("Hello", session_id="default")

# Chat in named session
await agent.chat("Hello", session_id="my_project")
```

### Session Persistence

```python
from agentry import SessionManager

sm = SessionManager()

# Save session
session = agent.get_session("my_project")
sm.save_session("my_project", session.messages)

# Load session
messages = sm.load_session("my_project")
if messages:
    session.messages = messages
```

---

## Session Structure

Each session contains:

| Field | Type | Description |
|:------|:-----|:------------|
| `session_id` | string | Unique identifier |
| `messages` | array | Full conversation history |
| `metadata` | object | Custom data |
| `created_at` | datetime | When session started |
| `last_activity` | datetime | Last interaction time |

---

## Interactive Mode

### Starting with Session

```bash
# Start with specific session
python run_agent.py --session my_project

# Resume existing session
python run_agent.py --session coding_task
```

### Session Commands

| Command | Description | Example |
|:--------|:------------|:--------|
| `/status` | Show current session info | `/status` |
| `/sessions` | List all sessions | `/sessions` |
| `/new <id>` | Create new session | `/new research` |
| `/resume <id>` | Resume session | `/resume my_project` |
| `/clear` | Clear current session | `/clear` |

### Example Workflow

```
$ python run_agent.py

[default] You: /new coding_task
Created new session: 'coding_task'

[coding_task] You: Create a factorial function
[coding_task] Assistant: [creates function]

[coding_task] You: /status
Current Session Status:
   Session ID: coding_task
   Messages: 3
   Created: 2025-11-22 20:30:15
   Last Activity: 2025-11-22 20:35:42
   Saved: Yes

[coding_task] You: /new research
Created new session: 'research'

[research] You: /resume coding_task
Resumed session: 'coding_task' (3 messages)
```

---

## Session Files

### Location

Sessions are stored in `agentry/session_history/`:

```
agentry/
└── session_history/
    ├── default_chat.toon
    ├── my_project_chat.toon
    └── coding_task_chat.toon
```

### File Format

Sessions use `.toon` format (JSON-based):

```json
{
    "session_id": "my_project",
    "created_at": "2025-11-22T20:30:15",
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful AI assistant..."
        },
        {
            "role": "user",
            "content": "Hello"
        },
        {
            "role": "assistant",
            "content": "Hi! How can I help?"
        }
    ]
}
```

---

## Multi-Session Management

### Programmatic Access

```python
from agentry import Agent, SessionManager

agent = Agent(llm="ollama")
sm = SessionManager()

sessions = ["project_a", "project_b", "research"]

for session_id in sessions:
    # Load or create session
    if sm.session_exists(session_id):
        messages = sm.load_session(session_id)
        session = agent.get_session(session_id)
        session.messages = messages
    
    # Work with session
    await agent.chat("Status update?", session_id=session_id)
    
    # Save
    session = agent.get_session(session_id)
    sm.save_session(session_id, session.messages)
```

### Session Metadata

```python
sessions = sm.list_sessions()

for s in sessions:
    print(f"ID: {s['id']}")
    print(f"Created: {s['created_at']}")
    print(f"Messages: {s['message_count']}")
    print()
```

---

## Advanced Features

### Custom Session Directory

```python
sm = SessionManager("my_custom_sessions/")
```

### Session Cleanup

```python
sessions = sm.list_sessions()
for s in sessions:
    if s['message_count'] == 0:
        sm.delete_session(s['id'])
```

### Session Export

```python
import json

messages = sm.load_session("my_project")
with open("export.json", "w") as f:
    json.dump(messages, f, indent=2)
```

### Session Import

```python
import json

with open("import.json", "r") as f:
    messages = json.load(f)

sm.save_session("imported_session", messages)
```

---

## Best Practices

### 1. Use Descriptive Session IDs

```python
# Good - descriptive and unique
session_id = "customer_support_2025_11_22"
session_id = "code_review_auth_module"

# Avoid - not meaningful
session_id = "session1"
session_id = "temp"
```

### 2. Regular Cleanup

```python
from datetime import datetime, timedelta

sessions = sm.list_sessions()
cutoff = datetime.now() - timedelta(days=30)

for s in sessions:
    created = datetime.fromisoformat(s['created_at'])
    if created < cutoff:
        sm.delete_session(s['id'])
```

### 3. Auto-Save Pattern

```python
# Save after important interactions
response = await agent.chat(user_input, session_id=session_id)
session = agent.get_session(session_id)
sm.save_session(session_id, session.messages)
```

### 4. Session Isolation

```python
# Use separate sessions for different contexts
await agent.chat("Debug this code", session_id="debugging")
await agent.chat("Write documentation", session_id="docs")
await agent.chat("Research topic", session_id="research")
```

### 5. Limit Session Size

```python
session = agent.get_session(session_id)
if len(session.messages) > 100:
    # Keep only recent messages
    session.messages = session.messages[-50:]
    sm.save_session(session_id, session.messages)
```

---

## Troubleshooting

### Session Not Found

```python
if not sm.session_exists(session_id):
    print(f"Session '{session_id}' not found")
    # Create new session
    agent.get_session(session_id)
```

### Corrupted Session File

```python
try:
    messages = sm.load_session(session_id)
except Exception as e:
    print(f"Error loading session: {e}")
    # Delete and recreate
    sm.delete_session(session_id)
    agent.get_session(session_id)
```

### Large Session Files

```python
session = agent.get_session(session_id)
if len(session.messages) > 100:
    # Clear old messages, keep recent
    session.messages = session.messages[-50:]
    sm.save_session(session_id, session.messages)
```

---

## Session Object Reference

### AgentSession Attributes

| Attribute | Type | Description |
|:----------|:-----|:------------|
| `session_id` | str | Unique identifier |
| `messages` | List[Dict] | Message history |
| `created_at` | datetime | Creation time |
| `last_activity` | datetime | Last activity time |
| `metadata` | Dict | Custom metadata |

### AgentSession Methods

**add_message(message)**

```python
session.add_message({"role": "user", "content": "Hello"})
```

**clear_history(keep_system=True)**

```python
session.clear_history(keep_system=True)
```

---

## SessionManager Reference

### Constructor

```python
SessionManager(history_dir: str = None)
```

### Methods

| Method | Returns | Description |
|:-------|:--------|:------------|
| `save_session(session_id, messages)` | None | Save session to file |
| `load_session(session_id)` | List[Dict] or None | Load session from file |
| `list_sessions()` | List[Dict] | List all sessions |
| `delete_session(session_id)` | bool | Delete session file |
| `session_exists(session_id)` | bool | Check if session exists |

---

## Next Steps

| Topic | Description |
|:------|:------------|
| [API Reference](api-reference) | Complete SessionManager API |
| [Examples](examples) | Session management examples |
| [Getting Started](getting-started) | Basic usage guide |
