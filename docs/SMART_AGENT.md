# Smart Agent Documentation

The **Smart Agent** is a new agent type in Agentry that provides enhanced reasoning, project memory, and learning capabilities. It's designed to be simple in operation but efficient in delivering results.

## Features

### 1. Two Operating Modes

#### Solo Mode (Default)
- Optimized for general reasoning and chat tasks
- Like ChatGPT/Gemini but with tool access
- Greater focus on step-by-step reasoning
- 5 essential tools only

```bash
# CLI
agentry --agent smart --mode solo

# Or just
agentry -a smart
```

#### Project Mode
- Centers attention on a specific project
- Maintains project context (title, goal, environment, key files)
- Stores project-specific learnings and approaches
- Automatically captures insights from conversations

```bash
# CLI with project
agentry --agent smart --mode project --project my_project
```

### 2. Essential Tools (5 Only)

The Smart Agent has exactly 5 tools - lean and focused:

| Tool | Description |
|------|-------------|
| `web_search` | Search the internet for information |
| `memory` | Store/retrieve learnings, approaches, patterns |
| `notes` | Personal note-taking (add, list, search, delete) |
| `datetime` | Get current date/time in multiple formats |
| `bash` | Execute shell commands |

### 3. Pluggable Project Memory

The memory system stores:
- **Approaches** - How to solve types of problems
- **Learnings** - Insights from conversations
- **Key Steps** - Important workflow steps
- **Patterns** - Reusable templates
- **Preferences** - User/project preferences
- **Decisions** - Key decisions made
- **Context** - Project-specific context

Memory is:
- **Persistent** - Stored in SQLite
- **Searchable** - Full-text search support
- **Exportable** - JSON or Markdown format for LLM context
- **Project-scoped** - Can be global or project-specific

## CLI Usage

```bash
# Smart Agent - Solo Mode (default)
agentry -a smart

# Smart Agent - Project Mode
agentry -a smart --mode project --project my-app

# With specific provider and model
agentry -a smart -p groq -m llama-3.3-70b-versatile

# With Ollama
agentry -a smart -p ollama -m llama3.2:3b

# Show help
agentry --help

# List available models
agentry --list-models
```

## API Endpoints

### Agent Configuration

```http
GET /api/agent/types
# Get available agent types

POST /api/agent/configure
# Configure agent type for user
{
  "agent_type": "smart",
  "mode": "solo" | "project",
  "project_id": "optional-project-id"
}

GET /api/agent/config
# Get current agent configuration
```

### Project Management

```http
GET /api/projects
# List all projects

POST /api/projects
# Create a new project
{
  "project_id": "my-project",
  "title": "My Project",
  "goal": "Build something amazing",
  "environment": {"language": "Python", "framework": "FastAPI"},
  "key_files": ["src/main.py", "config.yaml"]
}

GET /api/projects/{project_id}
# Get project details

PUT /api/projects/{project_id}/focus
# Update current focus
```

### Memory Management

```http
GET /api/memory
# Get memories (with optional filters)
?project_id=...&memory_type=...&limit=50

POST /api/memory
# Add a memory
{
  "memory_type": "learning",
  "title": "How to fix X",
  "content": "The solution is...",
  "tags": ["bug-fix", "python"],
  "project_id": "optional"
}

GET /api/memory/search?q=...
# Search memories

GET /api/memory/export
# Export memories for LLM context
?project_id=...&format=markdown

DELETE /api/memory/{memory_id}
# Delete a memory
```

## Python Usage

### Basic Usage

```python
import asyncio
from agentry.agents import SmartAgent

async def main():
    agent = SmartAgent(llm="ollama", model="llama3.2:3b")
    response = await agent.chat("What is the capital of France?")
    print(response)

asyncio.run(main())
```

### Creating a Project

```python
from agentry.agents import SmartAgent, SmartAgentMode

# Create Smart Agent
agent = SmartAgent(
    llm="groq",
    model="llama-3.3-70b-versatile",
    api_key="your-api-key",
    mode=SmartAgentMode.PROJECT,
    project_id="my-web-app"
)

# Create the project context
agent.create_project(
    project_id="my-web-app",
    title="My Web Application",
    goal="Build a FastAPI backend with React frontend",
    environment={"language": "Python", "framework": "FastAPI"},
    key_files=["main.py", "requirements.txt"]
)

# Chat with project context
response = await agent.chat("How should I structure the API endpoints?")
```

### Storing Learnings

```python
# Store a learning directly
await agent.remember(
    memory_type="approach",
    title="API Error Handling Pattern",
    content="Always use HTTPException with appropriate status codes...",
    tags=["api", "error-handling"]
)

# Search memories
memories = await agent.recall("error handling", limit=5)
```

### Exporting Context for Other LLMs

```python
# Get formatted context for injection into any LLM
context = agent.get_project_context_for_llm()
# Returns Markdown-formatted project context + memories

# Can also use the memory directly
from agentry.memory.project_memory import get_project_memory
memory = get_project_memory()
context = memory.export_for_llm(project_id="my-project", format="markdown")
```

## Architecture

```
SmartAgent
├── Inherits from Agent
├── ProjectMemory (SQLite)
│   ├── Projects table
│   ├── Memories table (with FTS5 search)
│   └── Export functions
├── 5 Essential Tools
│   ├── web_search
│   ├── memory
│   ├── notes
│   ├── datetime
│   └── bash
└── Mode-specific System Prompts
    ├── Solo Mode - General reasoning
    └── Project Mode - Context aware
```

## Best Practices

1. **Use Project Mode for focused work** - When working on a specific codebase or task
2. **Use Solo Mode for general queries** - For reasoning, research, or standalone questions
3. **Store valuable learnings** - Use the memory tool to capture insights
4. **Search before asking** - The agent can search its memory for past approaches
5. **Export context regularly** - Use `/api/memory/export` to backup learnings

## Future Enhancements

- [ ] Automatic learning extraction using LLM
- [ ] Memory importance scoring
- [ ] Cross-project memory sharing
- [ ] Vector search for semantic similarity
- [ ] Memory visualization in UI
