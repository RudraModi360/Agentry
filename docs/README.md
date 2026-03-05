# <i class="fas fa-cube" style="color: #673ab7;"></i> Logicore Documentation

Complete guide to the Logicore AI agent framework.

---

## <i class="fas fa-book" style="color: #673ab7;"></i> Documentation Sections

### **Getting Started**
- **[Bird's-Eye View](01-birds-eye-view.md)** — Conceptual overview for all stakeholders
- **[Quickstart](02-quickstart.md)** — Get up and running in 5 minutes

### **Building with Logicore**
- **[How-To Guides](03-how-to-guides.md)** — Multiple approaches for each task

### **Understanding the System**
- **[Core Architecture](04-core-architecture.md)** — How things work internally with Mermaid diagrams
- **[API Reference](05-api-reference.md)** — Complete class and method documentation

---

## <i class="fas fa-link" style="color: #673ab7;"></i> Quick Links

**For Decision Makers/Non-Technical:**
→ Start with [Bird's-Eye View](01-birds-eye-view.md)

**For Developers Getting Started:**
→ Go to [Quickstart](02-quickstart.md)

**For Building Features:**
→ Reference [How-To Guides](03-how-to-guides.md)

**For Deep Understanding:**
→ Read [Core Architecture](04-core-architecture.md)

**For Implementation Details:**
→ Check [API Reference](05-api-reference.md)

---

## <i class="fas fa-cube" style="color: #673ab7;"></i> What is Logicore?

Logicore is an AI agent framework that solves three critical problems:

1. **Persistent Memory** — Agents learn and remember across conversations
2. **Scalable Tool Management** — Handle tools from 1 to 1000+
3. **LLM Provider Flexibility** — Swap providers (OpenAI, Groq, Ollama, Azure, Gemini) with one line of code

---

## <i class="fas fa-cogs" style="color: #673ab7;"></i> Core Components

### <i class="fas fa-robot" style="color: #9c27b0;"></i> Agents
Create AI agents with memory, tools, and skills.
- `Agent` — Full-featured production agent
- `BasicAgent` — Simplified wrapper for getting started
- `CopilotAgent` — Pre-configured for coding tasks
- `MCPAgent` — Enterprise-scale with 100+ tools

### <i class="fas fa-database" style="color: #9c27b0;"></i> Memory
Persistent knowledge storage across sessions.
- `ProjectMemory` — Structured SQLite-based knowledge
- `AgentrySimpleMem` — Fast vector-based LanceDB storage

### <i class="fas fa-plug" style="color: #9c27b0;"></i> Providers
Unified interface for any LLM.
- OpenAI (GPT-4, GPT-3.5)
- Groq (Fast inference)
- Ollama (Local models)
- Azure OpenAI (Enterprise)
- Google Gemini

### <i class="fas fa-toolbox" style="color: #9c27b0;"></i> Tools
27+ built-in tools + custom tool support.
- Filesystem operations
- Code execution
- Web search & fetching
- Git operations
- Document handling (PDF, DOCX, Excel)
- Office tools

### <i class="fas fa-puzzle-piece" style="color: #9c27b0;"></i> Skills
Organized tool bundles for reuse.
- Load skills from filesystem
- Create custom skill packages
- Share skill libraries

---

## <i class="fas fa-download" style="color: #673ab7;"></i> Installation

```bash
pip install logicore
```

## <i class="fas fa-flash" style="color: #673ab7;"></i> 30-Second Example

```python
from logicore.agents import BasicAgent

agent = BasicAgent(provider="openai", model="gpt-4")
response = agent.chat("What's the weather like?")
print(response)
```

## <i class="fas fa-map" style="color: #673ab7;"></i> Navigation

| Document | Purpose | Audience |
|----------|---------|----------|
| [01-birds-eye-view.md](01-birds-eye-view.md) | Conceptual overview, analogies, business value | Stakeholders, non-technical |
| [02-quickstart.md](02-quickstart.md) | Get running in 5 minutes with examples | Developers starting out |
| [03-how-to-guides.md](03-how-to-guides.md) | Multiple approaches per task with decision trees | Developers building features |
| [04-core-architecture.md](04-core-architecture.md) | How the system works, with detailed flows | Advanced developers |
| [05-api-reference.md](05-api-reference.md) | Exhaustive class/method documentation | Reference during development |

---

## <i class="fas fa-life-ring" style="color: #673ab7;"></i> Help & Support

- **Questions?** Check the [FAQ in How-To Guides](03-how-to-guides.md#faq)
- **Stuck on a concept?** Read [Core Architecture](04-core-architecture.md)
- **Need a specific method?** See [API Reference](05-api-reference.md)

---

## <i class="fas fa-list" style="color: #673ab7;"></i> Table of Contents

- [Getting Started](#getting-started)
- [Building with Logicore](#building-with-logicore)
- [Understanding the System](#understanding-the-system)
- [What is Logicore?](#what-is-logicore)
- [Core Components](#core-components)
- [Installation](#installation)
- [30-Second Example](#30-second-example)

---

## <i class="fas fa-heart" style="color: #673ab7;"></i> Special Thanks

Logicore is built upon the shoulders of giants. We'd like to extend our gratitude to:

- **[SimpleMem](https://github.com/lancedb/lancedb)** — Fast vector-based embedding and storage for intelligent memory management
- **[MCP (Model Context Protocol)](https://github.com/anthropics/mcp)** — Enterprise-scale tool orchestration and standardized model interactions
- **[Ollama](https://github.com/ollama/ollama)** — Enabling powerful local model inference without cloud dependencies
- **[Groq](https://github.com/groq/groq-python)** — Lightning-fast LLM inference for real-time agent responses

These technologies are fundamental to Logicore's performance, flexibility, and accessibility.

---

**Logicore v1.0.0** 

